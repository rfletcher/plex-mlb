import re, sys, urllib, datetime, pytz

# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

# MLB modules
from . import Config, Util
from .Classes import Game, TeamList

teams = TeamList.TeamList(Config.TEAMS)

Prefs.Add(id='team', type='enum', default='(None)', label='Favorite Team', values=teams.toOptions())
Prefs.Add(id='login', type='text', default='', label='MLB.com Login')
Prefs.Add(id='password', type='text', default='', label='MLB.com Password', option='hidden')
Prefs.Add(id='allowspoilers', type='bool', default='true', label='Show spoilers for finished games')

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(Config.PLUGIN_PREFIX, Menu, "<%= PLUGIN_NAME %>")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

  # default MediaContainer properties
  MediaContainer.title1 = '<%= PLUGIN_NAME %>'
  MediaContainer.viewGroup = 'List'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')

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

  for entry in XML.ElementFromURL(Config.URL_TOP_VIDEOS).xpath('item'):
    id = entry.get('cid')
    title = entry.xpath('title')[0].text
    desc = entry.xpath('big_blurb')[0].text
    duration = int(Util.parseDuration(entry.xpath('duration')[0].text)) * 1000
    thumb = entry.xpath("pictures/picture[@type='small-text-graphic']/url")[0].text

    dir.Append(_getHighlightVideoItem(id, title, desc, duration, thumb))

  return dir

####################################################################################################
def HighlightSearchResultsMenu(sender, query=None):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  dir = _populateFromSearch(dir, {"text": query})

  return dir

####################################################################################################
def _MLBTVGamesList(dir):
  # get game list URL
  time = datetime.datetime.now(pytz.timezone("US/Eastern"))
  if time.hour < 10:
    time = time - datetime.timedelta(days=1)
  urltokens = (time.year, "%02d" % time.month, "%02d" % time.day)

  items = []
  # load the game list from the populated url
  for xml in XML.ElementFromURL(Config.URL_MLBTV_GAMES % urltokens).xpath('game'):
    item = { 'game': Game.fromXML(xml, teams) }
    if item['game'].event_id:
      item['video_url'] = 'http://mlb.mlb.com/flash/mediaplayer/v4/RC12/MP4.jsp?calendar_event_id=' + item['game'].event_id
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
    dir.Append(Function(DirectoryItem(itemFunction, Config.FAVORITE_MARKER + favoriteteam.fullName()), query=favoriteteam.id, **kwargs))

  for team in teams:
    if not favoriteteam or favoriteteam != team:
      dir.Append(Function(DirectoryItem(itemFunction, team.fullName()), query=team.id, **kwargs))

  return dir

####################################################################################################
def _getHighlightVideoItem(id, title, desc, duration, thumb):
  (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
  subtitle = "posted %s/%s/%s" % (month, day, year)

  xml = XML.ElementFromURL(Config.URL_GAME_DETAIL % (year, month, day, content_id))
  url = xml.xpath('//url[@playback_scenario="MLB_FLASH_800K_PROGDNLD"]')[0].text

  return VideoItem(url, title, subtitle=subtitle, summary=desc, duration=duration, thumb=thumb)

####################################################################################################
def _populateFromSearch(dir,query):
  params = Config.SEARCH_PARAMS.copy()
  params.update(query)
  json = JSON.ObjectFromURL(Config.URL_SEARCH + '?' + urllib.urlencode(params))
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
