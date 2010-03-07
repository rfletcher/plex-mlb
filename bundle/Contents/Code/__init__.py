import re, sys, urllib, datetime, pytz, isodate

# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

# MLB modules
from .Config import _C
from .Classes import Game, TeamList
from . import Util

teams = TeamList.TeamList(_C["TEAMS"])

####################################################################################################
def Start():
  # default MediaContainer properties
  MediaContainer.title1 = _C["PLUGIN_NAME"]
  MediaContainer.viewGroup = 'List'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')
  WebVideoItem.thumb = R('icon-video-default.png')

  # default cache time
  HTTP.SetCacheTime(_C["CACHE_TTL"])

  # Prefetch some content
  HTTP.PreCache(_GameListURL(), cacheTime=_C["GAME_CACHE_TTL"])

  Plugin.AddPrefixHandler(_C["PLUGIN_PREFIX"], MainMenu, _C["PLUGIN_NAME"], 'icon-default.png', 'art-default.jpg')
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

####################################################################################################
def CreatePrefs():
  Prefs.Add('team', type='enum', default='(None)', label='Favorite Team', values=teams.toOptions())
  Prefs.Add('login', type='text', default='', label='MLB.com Login')
  Prefs.Add('password', type='text', default='', label='MLB.com Password', option='hidden')
  Prefs.Add('allowspoilers', type='bool', default="true", label='Show spoilers for in-progress and completed games')

####################################################################################################
def UpdateCache():
  HTTP.Request(_C["URL"]["TOP_VIDEOS"])

####################################################################################################
def MLBTVMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  dir = _MLBTVGamesList(dir)
  return dir

####################################################################################################
def FeaturedHighlightsMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  for entry in XML.ElementFromURL(_C["URL"]["TOP_VIDEOS"]).xpath('item'):
    id = entry.get('content_id')
    title = entry.xpath('title')[0].text
    summary = entry.xpath('big_blurb')[0].text
    duration = int(Util.parseDuration(entry.xpath('duration')[0].text)) * 1000
    thumb = entry.xpath("pictures/picture[@type='dam-raw-thumb']/url")[0].text
    url = entry.xpath("url[@speed=1000]")[0].text

    dir.Append(_getHighlightVideoItem(id, url=url, title=title, summary=summary, duration=duration, thumb=thumb))

  return dir

####################################################################################################
def _MediaListURL():
  return _DateURL(_C["URL"]["MEDIA"])

####################################################################################################
def _GameListURL():
  return _DateURL(_C["URL"]["GAMES"])

####################################################################################################
def _DateURL(url):
  time = datetime.datetime.now(pytz.timezone("US/Eastern"))
  if time.hour < 10:
    time = time - datetime.timedelta(days=1)
  return url % (time.year, "%02d" % time.month, "%02d" % time.day)

####################################################################################################
def _MediaStreams():
  table_columns = _C["MEDIA_COLUMNS"]
  events = {}

  # parse some HTML
  for row in XML.ElementFromURL(_MediaListURL(), True, encoding='ISO-8859-1').cssselect('.mmg_table tbody tr'):
    event_id = row.get('id')
    streams = {}

    cells = row.cssselect('td')
    for i in range(0, len(table_columns)):
      stream_type = table_columns[i]
      cell = cells[i]

      if stream_type == None or cell.text_content() == '':
        continue
      else:
        label = cell.text_content()
        content_id = cell.get('id')
        if not len(cell.cssselect('a')): continue

        if label and content_id:
          streams[stream_type] = {'label': label, 'id': content_id}

    events[event_id] = streams

  return events

####################################################################################################
def _MLBTVGamesList(dir):
  # only pull the media list if the preference that needs it is in play
  streams = {}
  if teams.findByFullName(Prefs.Get('team')) != None:
    streams = _MediaStreams()

  items = []
  # load the game list from the populated url
  for xml in XML.ElementFromURL(_GameListURL(), cacheTime=_C["GAME_CACHE_TTL"]).xpath('game'):
    game = Game.fromXML(xml, teams)
    if streams: game.streams = streams[game.event_id]

    item = {
      'game': game,
      'video_url': _C["URL"]["PLAYER"] + "?" + urllib.urlencode({
        'calendar_event_id': game.event_id,
        'content_id': game.getContentID() 
      })
    }
    items.append(item)

  # move favorite team's game(s) to the top
  for i, item in enumerate(items):
    if item['game'].home_team.isFavorite() or item['game'].away_team.isFavorite():
      items.insert(0, items.pop(i))

  # add the games as menu items
  for item in items:
    try:
      dir.Append(WebVideoItem(item['video_url'], item['game'].getMenuLabel(), subtitle=item['game'].getSubtitle(), summary=item['game'].getDescription()))
    except KeyError:
      Log('no video: ' + item['game'].getMenuLabel())
      dir.Append(MessageItem(item['game'].getMenuLabel(), "No Video", "There is no video available for this game.",  subtitle=item['game'].getSubtitle(), summary=item['game'].getDescription()))

  return dir

####################################################################################################
def _getHighlightVideoItem(id, url=None, title=None, subtitle=None, summary=None, duration=None, thumb=None):
  # (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
  # subtitle = None #"posted %s/%s/%s" % (month, day, year)
  xml = None

  if None in [url, title, subtitle, summary, duration, thumb]:
    xurl = _C["URL"]["GAME_DETAIL"] % (id[-3], id[-2], id[-1], id)
    xml = XML.ElementFromURL(xurl, headers={"Referer": Util.getURLRoot(xurl)})

  if url is None:
    for scenario in ["MLB_FLASH_1000K_PROGDNLD", "MLB_FLASH_800K_PROGDNLD", "MLB_FLASH_1000K_STREAM_VPP", "MLB_FLASH_800K_STREAM_VPP"]:
      url = Util.XPathSelectOne(xml, 'url[@playback_scenario="' + scenario + '"]')
      if url is not None:
        break
    else:
      # couldn't find a URL
      return

  if duration is None:
    duration_string = Util.XPathSelectOne(xml, 'duration')
    if duration_string is not None:
      duration = int(Util.parseDuration(duration_string)) * 1000
  if title is None:
    title = Util.XPathSelectOne(xml, 'headline')
  if subtitle is None:
    date = isodate.parse_datetime(Util.XPathSelectOne(xml, '//@date'))
    # Log(date.astimezone(datetime.datetime.now().tzinfo))
    # subtitle = date.strftime("%a, %d %b %Y %H:%M:%S %Z")
    subtitle = date.strftime("%A, %B %d")

  if summary is None:
    summary = re.sub("^\s*(\d+\.){2}\d+\:", "", str(Util.XPathSelectOne(xml, 'big-blurb')))
  if thumb is None:
    thumb = Util.XPathSelectOne(xml, 'thumbnailScenarios/thumbnailScenario[@type="7"]')

  if url[:7] == "rtmp://":
    # pass clip as an empty string to prevent an exception
    return RTMPVideoItem(url, clip="", title=title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)
  else:
    return VideoItem(url, title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)

####################################################################################################
def _populateFromSearch(dir, query):
  params = _C["SEARCH_PARAMS"].copy()
  params.update(query)

  url = _C["URL"]["SEARCH"] +'?' + urllib.urlencode(params)
  json = JSON.ObjectFromURL(url, headers={"Referer": Util.getURLRoot(url)})

  if json['total'] < 1:
    return ShowMessage(None, 'No Results', 'No results were found.')

  else:
    for entry in json['mediaContent']:
      dir.Append(_getHighlightVideoItem(entry['contentId']))

  return dir





def MenuHandler(sender, cls=None, **kwargs):
  """
  A menu class factory.  The Plex Function() wrapper doesn't seem to like classes as arguments.
  TODO: I'm not convinced that this function is necessary. Investigate further.
  """
  return cls(sender, **kwargs)


# abstract
class Menu(MediaContainer):
  def __init__(self, **kwargs):
    MediaContainer.__init__(self, **kwargs)

  def AddMenu(self, menuClass, title, **kwargs):
    self.Append(Function(DirectoryItem(MenuHandler, title), cls=menuClass, **kwargs))

  def AddPreferences(self, title="Preferences"):
    self.Append(PrefsItem(title))

  def AddSearch(self, menuClass, title="Search", message=None, **kwargs):
    message = message if message is not None else title
    self.Append(Function(SearchDirectoryItem(MenuHandler, title, message, thumb=R("search.png")), cls=menuClass, **kwargs))

  def AddMessage(self, message, title=_C['PLUGIN_NAME']):
    self.AddMenu(Message, title, message=message)

  def ShowMessage(self, message, title=_C['PLUGIN_NAME']):
    MediaContainer.__init__(self, header=title, message=message)


class Message(Menu):
  def __init__(self, sender, message=None, **kwargs):
    Menu.__init__(self)
    self.ShowMessage(message, **kwargs)


class MainMenu(Menu):
  def __init__(self):
    Menu.__init__(self)
    self.AddMenu(HighlightsMenu, 'Highlights')
    self.AddMenu(MLBTVMenu, 'MLB.tv')
    self.AddPreferences()


class HighlightsMenu(Menu):
  def __init__(self, sender):
    Menu.__init__(self)
    self.AddMenu(FeaturedHighlightsMenu, 'Featured Highlights')
    self.AddMenu(TeamListMenu, 'Team Highlights')
    self.AddMenu(HighlightsSearchMenu, 'MLB.com FastCast', query='FastCast')
    self.AddMenu(HighlightsSearchMenu, 'MLB Network')
    self.AddMenu(HighlightsSearchMenu, 'Plays of the Day')
    self.AddSearch(HighlightsSearchMenu, title='Search Highlights')


class HighlightsSearchMenu(Menu):
  def __init__(self, sender, teamId=None, query=None):
    Menu.__init__(self, viewGroup='Details', title2=sender.itemTitle)

    params = _C["SEARCH_PARAMS"].copy()
    if teamId is not None:
      params.update({"team_id": teamId})
    else:
      params.update({"text": query if query is not None else sender.itemTitle})

    url = _C["URL"]["SEARCH"] + '?' + urllib.urlencode(params)
    json = JSON.ObjectFromURL(url, headers={"Referer": Util.getURLRoot(url)})

    if json['total'] < 1:
      self.ShowMessage('No results were found.', title='No Results')
    else:
      for entry in json['mediaContent']:
        self.Append(_getHighlightVideoItem(entry['contentId']))


class TeamListMenu(Menu):
  def __init__(self, sender):
    Menu.__init__(self, title2=sender.itemTitle)

    favoriteteam = teams.findByFullName(Prefs.Get('team'))
    if favoriteteam:
      self.AddMenu(HighlightsSearchMenu, _C["FAVORITE_MARKER"] + favoriteteam.fullName(), teamId=favoriteteam.id)

    for team in teams:
      if not favoriteteam or favoriteteam != team:
        self.AddMenu(HighlightsSearchMenu, team.fullName(), teamId=team.id)
