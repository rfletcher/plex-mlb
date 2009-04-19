import re, sys, urllib, time

# PMS plugin framework
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

# MLB modules
from . import Config, Util
from .Classes import Game, TeamList

teams = TeamList.TeamList(Config.Teams)

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(Config.PLUGIN_PREFIX, Menu, "Major League Baseball")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

  AddPreferences()

  # default MediaContainer properties
  MediaContainer.title1 = 'Major League Baseball'
  MediaContainer.viewGroup = 'List'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')

####################################################################################################
def AddPreferences():
  Prefs.Add(id='team', type='enum', default='(None)', label='Favorite Team', values=teams.toOptions())
  Prefs.Add(id='login', type='text', default='', label='MLB.com Login')
  Prefs.Add(id='password', type='text', default='', label='MLB.com Password', option='hidden')
  Prefs.Add(id='spoilers', type='bool', default='true', label='Show spoilers for finished games')

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
  dir.Append(Function(SearchDirectoryItem(HighlightSearchResultsMenu, 'Search Highlights', 'Search Highlights', thumb=R("search.png"))))
  return dir

####################################################################################################
def MLBTVMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
  dir = MLBTVGamesList(dir)
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
def MLBTVGamesList(dir):
  # get game list URL
  # TODO get the current date/time and populate these values
  tm = time.localtime()
  urlvals = { 'year': str(tm[0]), 'month': "%02d" % tm[1], 'day': "%02d" % tm[2] }
  urlsubs = { 'year': '%y', 'month': '%m', 'day': '%d' }
  game_list_url = 'http://mlb.mlb.com/mobile/data/atbatScoreboard2009.jsp?y=%y&m=%m&d=%d'

  # replace url tokens with values from urlvars
  for (name, token) in urlsubs.items():
    game_list_url = game_list_url.replace(token, urlvals[name])

  # load the game list from the populated url
  for xml in XML.ElementFromURL(game_list_url).xpath('game'):
    game = Game.fromXML(xml, teams)

    if len(game.event_id):
      video_url = 'http://mlb.mlb.com/flash/mediaplayer/v4/RC9/MP4.jsp?calendar_event_id=' + game.event_id
      dir.Append(WebVideoItem(video_url, game.getMenuLabel(), subtitle=game.getSubtitle(), summary=game.getDescription()))
    else:
      Log(game.getMenuLabel())
      # dir.Append(MessageContainer('No Results', 'No results were found.'))
      dir.Append(DirectoryItem("503", game.getMenuLabel(), subtitle=game.getSubtitle(), summary=game.getDescription()))

  return dir

####################################################################################################
def TeamHighlightsMenu(sender, query=None):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  return _populateFromSearch(dir, {"team_id": query})

####################################################################################################
def TeamListMenu(sender, itemFunction=None, **kwargs):
  dir = MediaContainer(title2=sender.itemTitle)

  favoriteteam = teams.findById(Prefs.Get('team'))
  if favoriteteam:
    dir.Append(Function(DirectoryItem(itemFunction, "* " + favoriteteam.fullName()), query=favoriteteam.id, **kwargs))

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
    return MessageContainer('No Results', 'No results were found.')
    # dir.SetMessage('No Results', 'No results were found.')

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
