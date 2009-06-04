import re, sys, urllib, datetime, pytz

# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

# MLB modules
from .Config import _C
from .Classes import Game, TeamList
from . import Util

teams = TeamList.TeamList(_C["TEAMS"])

Prefs.Add(id='team', type='enum', default='(None)', label='Favorite Team', values=teams.toOptions())
Prefs.Add(id='login', type='text', default='', label='MLB.com Login')
Prefs.Add(id='password', type='text', default='', label='MLB.com Password', option='hidden')
Prefs.Add(id='allowspoilers', type='bool', default='true', label='Show spoilers for finished games')

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(_C["PLUGIN_PREFIX"], Menu, _C["PLUGIN_NAME"])
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

  # default MediaContainer properties
  MediaContainer.title1 = _C["PLUGIN_NAME"]
  MediaContainer.viewGroup = 'List'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')

  # default cache time
  HTTP.SetCacheTime(_C["CACHE_TTL"])

  # Prefetch some content
  HTTP.PreCache(_GameListURL(), cacheTime=_C["GAME_CACHE_TTL"])

####################################################################################################
def UpdateCache():
  HTTP.Request(_C["URL"]["TOP_VIDEOS"])

####################################################################################################
def Menu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(HighlightsMenu, 'Highlights')))
  dir.Append(Function(DirectoryItem(MLBTVMenu, 'MLB.tv')))
  dir.Append(PrefsItem(title="Preferences"))
  return dir

####################################################################################################
def HighlightsMenu(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  dir.Append(Function(DirectoryItem(FeaturedHighlightsMenu, 'Featured Highlights')))
  dir.Append(Function(DirectoryItem(TeamListMenu,'Team Highlights'), itemFunction=TeamHighlightsMenu))

  for search in [['MLB.com FastCast', 'FastCast'], 'MLB Network', 'Plays of the Day']:
    if isinstance(search, list):
      label = search[0]
      query = '"%s"' % search[1]
    else:
      label = search
      query = '"%s"' % search
    dir.Append(Function(DirectoryItem(HighlightSearchResultsMenu, label), query=query))

  dir.Append(Function(SearchDirectoryItem(HighlightSearchResultsMenu, 'Search Highlights', 'Search Highlights', thumb=R("search.png"))))
  return dir

####################################################################################################
def MLBTVMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  dir = _MLBTVGamesList(dir)
  return dir

####################################################################################################
def FeaturedHighlightsMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  for entry in XML.ElementFromURL(_C["URL"]["TOP_VIDEOS"]).xpath('item'):
    id = entry.get('cid')
    title = entry.xpath('title')[0].text
    desc = entry.xpath('big_blurb')[0].text
    duration = int(Util.parseDuration(entry.xpath('duration')[0].text)) * 1000
    thumb = entry.xpath("pictures/picture[@type='small-text-graphic']/url")[0].text

    dir.Append(_getHighlightVideoItem(id, title, desc, duration, thumb))

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
def HighlightSearchResultsMenu(sender, query=None):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  dir = _populateFromSearch(dir, {"text": query})

  return dir

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
def TeamHighlightsMenu(sender, query=None):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  return _populateFromSearch(dir, {"team_id": query})

####################################################################################################
def TeamListMenu(sender, itemFunction=None, **kwargs):
  dir = MediaContainer(title2=sender.itemTitle)

  favoriteteam = teams.findByFullName(Prefs.Get('team'))
  if favoriteteam:
    dir.Append(Function(DirectoryItem(itemFunction, _C["FAVORITE_MARKER"] + favoriteteam.fullName()), query=favoriteteam.id, **kwargs))

  for team in teams:
    if not favoriteteam or favoriteteam != team:
      dir.Append(Function(DirectoryItem(itemFunction, team.fullName()), query=team.id, **kwargs))

  return dir

####################################################################################################
def _getHighlightVideoItem(id, title, desc, duration, thumb):
  (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
  subtitle = "posted %s/%s/%s" % (month, day, year)

  xml = XML.ElementFromURL(_C["URL"]["GAME_DETAIL"] % (year, month, day, content_id))
  url = xml.xpath('//url[@playback_scenario="MLB_FLASH_800K_PROGDNLD"]')[0].text

  return VideoItem(url, title, subtitle=subtitle, summary=desc, duration=duration, thumb=thumb)

####################################################################################################
def _populateFromSearch(dir,query):
  params = _C["SEARCH_PARAMS"].copy()
  params.update(query)
  json = JSON.ObjectFromURL(_C["URL"]["SEARCH"] + '?' + urllib.urlencode(params))
  del params

  if json['total'] < 1:
    return ShowMessage(None, 'No Results', 'No results were found.')

  else:
    for entry in json['mediaContent']:
      id = entry['mid']
      duration = Util.parseDuration(entry['duration'])
      title = entry['blurb']
      desc = entry['bigBlurb']
      thumb = entry['thumbnails'][0]['src']

      try:
        dir.Append(_getHighlightVideoItem(id, title, desc, duration, thumb))
      except:
        pass

  return dir

####################################################################################################
def MessageItem(title, messagetitle="Error", message="Error", **kwargs):
  return Function(DirectoryItem(ShowMessage, title, **kwargs), title=title, message=message)

####################################################################################################
def ShowMessage(sender, title="Error", message="Error"):
  return MessageContainer(title, message)
