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
    # TODO this seems fragile.  investigate another way.
    for scenario in [
      "FLASH_1000K_640X360",
      "MLB_FLASH_1000K_PROGDNLD",
      "MLB_FLASH_1000K_STREAM_VPP",
      "FLASH_800K_640X360",
      "MLB_FLASH_800K_PROGDNLD",
      "MLB_FLASH_800K_STREAM_VPP",
      "FLASH_400K_600X338"
    ]:
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
    thumb = Util.XPathSelectOne(xml, 'thumbnailScenarios/thumbnailScenario[@type="3"]')

  if url[:7] == "rtmp://":
    # pass clip as an empty string to prevent an exception
    return RTMPVideoItem(url, clip="", title=title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)
  else:
    return VideoItem(url, title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)




def MenuHandler(sender, cls=None, **kwargs):
  """
  A menu class factory.  The Plex Function() wrapper doesn't seem to like classes as arguments.
  TODO: I'm not convinced that this function is necessary. Investigate further.
  """
  return cls(sender, **kwargs)


# abstract
class Menu(MediaContainer):
  """
  Menu base class.
  """
  def __init__(self, **kwargs):
    """
    Initialize a Menu.  Child classes must call Menu.__init__()
    """
    MediaContainer.__init__(self, **kwargs)

  def AddMenu(self, menuClass, title, **kwargs):
    """
    Add a menu item which opens a submenu.
    """
    self.Append(Function(DirectoryItem(MenuHandler, title), cls=menuClass, **kwargs))

  def AddPreferences(self, title="Preferences"):
    """
    Add a menu item which opens the preferences dialog.
    """
    self.Append(PrefsItem(title))

  def AddSearch(self, menuClass, title="Search", message=None, **kwargs):
    """
    Add a menu item which opens a search dialog.
    """
    message = message if message is not None else title
    self.Append(Function(SearchDirectoryItem(MenuHandler, title, message, thumb=R("search.png")), cls=menuClass, **kwargs))

  def AddMessage(self, message, title=_C['PLUGIN_NAME']):
    """
    Add a menu item which opens a message dialog.
    """
    self.AddMenu(Message, title, message=message)

  def ShowMessage(self, message, title=_C['PLUGIN_NAME']):
    """
    Show a message immediately.
    """
    MediaContainer.__init__(self, header=title, message=message)


class Message(Menu):
  """
  A Menu which displays a message.
  """
  def __init__(self, sender, message=None, **kwargs):
    Menu.__init__(self)
    self.ShowMessage(message, **kwargs)


class MainMenu(Menu):
  """
  The top-level menu
  """
  def __init__(self):
    """
    Initialize the menu with menu items.
    """
    Menu.__init__(self)
    self.AddMenu(HighlightsMenu, 'Highlights')
    self.AddMenu(MLBTVMenu, 'MLB.tv')
    self.AddPreferences()


class FeaturedHighlightsMenu(Menu):
  """
  The highlights/featured Menu
  """
  def __init__(self, sender):
    """
    Fetch a list of featured highlights from mlb.com, adding each to the menu.
    """
    Menu.__init__(self)
    for entry in XML.ElementFromURL(_C["URL"]["TOP_VIDEOS"]).xpath('item'):
      id = entry.get("content_id")
      title = Util.XPathSelectOne(entry, "title")
      summary = Util.XPathSelectOne(entry, "big_blurb")
      duration = int(Util.parseDuration(Util.XPathSelectOne(entry, "duration"))) * 1000
      thumb = Util.XPathSelectOne(entry, "pictures/picture[@type='dam-raw-thumb']/url")
      url = Util.XPathSelectOne(entry, "url[@speed=1000]")

      self.Append(_getHighlightVideoItem(id, url=url, title=title, summary=summary, duration=duration, thumb=thumb))


class HighlightsMenu(Menu):
  """
  The highlights/ Menu
  """
  def __init__(self, sender):
    Menu.__init__(self)
    self.AddMenu(FeaturedHighlightsMenu, 'Featured Highlights')
    self.AddMenu(TeamListMenu, 'Team Highlights', submenu=HighlightsSearchMenu)
    self.AddMenu(HighlightsSearchMenu, 'MLB.com FastCast', query='FastCast')
    self.AddMenu(HighlightsSearchMenu, 'MLB Network')
    self.AddMenu(HighlightsSearchMenu, 'Plays of the Day')
    self.AddSearch(HighlightsSearchMenu, title='Search Highlights')


class HighlightsSearchMenu(Menu):
  """
  A Menu of highlights search results.
  """
  def __init__(self, sender, teamId=None, query=None):
    """
    Search mlb.com highlights for either a query, or a team ID, adding each
    result to the menu.
    """
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
  """
  A Menu consisting of a list of teams.
  """
  def __init__(self, sender, submenu=None):
    """
    List teams, displaying the 'submenu' Menu when selected.
    """
    Menu.__init__(self, title2=sender.itemTitle)

    favoriteteam = teams.findByFullName(Prefs.Get('team'))
    if favoriteteam:
      self.AddMenu(submenu, _C["FAVORITE_MARKER"] + favoriteteam.fullName(), teamId=favoriteteam.id)

    for team in teams:
      if not favoriteteam or favoriteteam != team:
        self.AddMenu(submenu, team.fullName(), teamId=team.id)
