import re, sys, time, urllib
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

# plugin config

MLB_PLUGIN_PREFIX = '/video/mlb'

# mlb.com config

MLB_URL_ROOT   = 'http://mlb.mlb.com'

# JSON media search (nice work, MLB :)
MLB_URL_SEARCH = MLB_URL_ROOT + '/ws/search/MediaSearchService'
MLB_SEARCH_PARAMS = { "type" : "json", "start": 1, "hitsPerPage": 12, "ns": 1 }

# XML files
MLB_URL_GAME_DETAIL = MLB_URL_ROOT + '/gen/multimedia/detail/%s/%s/%s/%s.xml'
MLB_URL_TOP_VIDEOS  = MLB_URL_ROOT + '/gen/mlb/components/multimedia/topvideos.xml'
MLB_URL_EPG_SERVICES = MLB_URL_ROOT + '/flash/mediaplayer/v4/RC5/xml/epg_services.xml'

MLB_TEAMS = [
  { 'id': '109', 'city': 'Arizona',       'name': 'Diamondbacks' },
  { 'id': '144', 'city': 'Atlanta',       'name': 'Braves' },
  { 'id': '110', 'city': 'Baltimore',     'name': 'Orioles' },
  { 'id': '111', 'city': 'Boston',        'name': 'Red Sox' },
  { 'id': '112', 'city': 'Chicago',       'name': 'Cubs' },
  { 'id': '145', 'city': 'Chicago',       'name': 'White Sox' },
  { 'id': '113', 'city': 'Cincinnati',    'name': 'Reds' },
  { 'id': '114', 'city': 'Cleveland',     'name': 'Indians' },
  { 'id': '115', 'city': 'Colorado',      'name': 'Rockies' },
  { 'id': '116', 'city': 'Detroit',       'name': 'Tigers' },
  { 'id': '146', 'city': 'Florida',       'name': 'Marlins' },
  { 'id': '117', 'city': 'Houston',       'name': 'Astros' },
  { 'id': '118', 'city': 'Kansas City',   'name': 'Royals' },
  { 'id': '108', 'city': 'Los Angeles',   'name': 'Angels' },
  { 'id': '119', 'city': 'Los Angeles',   'name': 'Dodgers' },
  { 'id': '158', 'city': 'Milwaukee',     'name': 'Brewers' },
  { 'id': '142', 'city': 'Minnesota',     'name': 'Twins' },
  { 'id': '121', 'city': 'New York',      'name': 'Mets' },
  { 'id': '147', 'city': 'New York',      'name': 'Yankees' },
  { 'id': '133', 'city': 'Oakland',       'name': 'Athletics' },
  { 'id': '143', 'city': 'Philadelphia',  'name': 'Phillies' },
  { 'id': '134', 'city': 'Pittsburgh',    'name': 'Pirates' },
  { 'id': '135', 'city': 'San Diego',     'name': 'Padres' },
  { 'id': '137', 'city': 'San Francisco', 'name': 'Giants' },
  { 'id': '136', 'city': 'Seattle',       'name': 'Mariners' },
  { 'id': '138', 'city': 'St. Louis',     'name': 'Cardinals' },
  { 'id': '139', 'city': 'Tampa Bay',     'name': 'Rays' },
  { 'id': '140', 'city': 'Texas',         'name': 'Rangers' },
  { 'id': '141', 'city': 'Toronto',       'name': 'Blue Jays' },
  { 'id': '120', 'city': 'Washington',    'name': 'Nationals' }
]

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(MLB_PLUGIN_PREFIX, Menu, "Major League Baseball", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

  AddPreferences()

  # default MediaContainer properties
  MediaContainer.title1 = 'Major League Baseball'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('art-default.jpg')

####################################################################################################
def AddPreferences():
  options = MLB_TEAMS[:]
  options.reverse()
  values = '(None)|'
  for team in options:
    values += ( team['city'] + ' ' + team['name'] + '|' )
  del options

  Prefs.Add( id='team', type='enum', default='(None)', label='Favorite Team', values=values)
  Prefs.Add( id='login', type='text', default='', label='MLB.com Login')
  Prefs.Add( id='password', type='text', default='', label='MLB.com Password', option='hidden')

####################################################################################################
def Menu():
  dir = MediaContainer()
  dir.Append(Function(DirectoryItem(HighlightsMenu, 'Highlights')))
  dir.Append(Function(DirectoryItem(MLBTVMenu, 'MLB.tv')))
  dir.Append(PrefsItem(title="Preferences"))
  return dir

####################################################################################################
def HighlightsMenu(sender):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)
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

  for entry in XML.ElementFromURL(MLB_URL_TOP_VIDEOS).xpath('item'):
    id = entry.get('cid')
    title = entry.xpath('title')[0].text
    desc = entry.xpath('big_blurb')[0].text
    duration = HMSDurationToMilliseconds(entry.xpath('duration')[0].text)
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
  urlvars = { 'year': '2009', 'month': '04', 'day': '11' }

  service = XML.ElementFromURL(MLB_URL_EPG_SERVICES).xpath("*[@id='loadTodayGames']")[0]
  game_list_url = service.xpath('./@url')[0]
  urlsubs = JSON.ObjectFromString(service.xpath('./@map')[0])

  # replace url tokens with values from urlvars
  for (name, token) in urlsubs.items():
    game_list_url = game_list_url.replace( token, urlvars[name] )

  # load the game list from the populated url
  for game in XML.ElementFromURL(game_list_url).xpath('game'):
    home_team = findTeamById(game.xpath('./@home_team_id')[0])
    away_team = findTeamById(game.xpath('./@away_team_id')[0])
    event_id = game.xpath('game_media/media/@calendar_event_id')

    label = away_team['name'] + ' @ ' + home_team['name']
    desc = "description"

    if len(event_id):
      video_url = 'http://mlb.mlb.com/flash/mediaplayer/v4/RC9/MP4.jsp?calendar_event_id=' + event_id[0]
      dir.Append(WebVideoItem(video_url, label, desc, "", None))
    else:
      dir.Append(DirectoryItem("503", label, desc))

  return dir

####################################################################################################
def TeamHighlightsMenu(sender, query=None):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  return _populateFromSearch(dir, {"team_id": query})

####################################################################################################
def TeamListMenu(sender, itemFunction=None, **kwargs):
  dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle)

  favoriteteam = findTeamById(Prefs.Get('team'))
  if favoriteteam:
    dir.Append(Function(DirectoryItem(itemFunction, "* " + favoriteteam["city"] + ' ' + favoriteteam["name"]), query=favoriteteam["id"], **kwargs))

  for team in MLB_TEAMS:
    if not favoriteteam or favoriteteam != team:
      dir.Append(Function(DirectoryItem(itemFunction, team["city"] + ' ' + team["name"]), query=team["id"], **kwargs))

  return dir

####################################################################################################
def _getHighlightVideoItem(id, title, desc, duration, thumb):
  (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
  subtitle = "posted %s/%s/%s" % (month, day, year)

  xml = XML.ElementFromURL(MLB_URL_GAME_DETAIL % (year, month, day, content_id))
  url = xml.xpath('//url[@playback_scenario="MLB_FLASH_800K_PROGDNLD"]')[0].text

  return VideoItem(url, title, subtitle=subtitle, summary=desc, duration=duration, thumb=thumb)

####################################################################################################
def _populateFromSearch(dir,query):
  params = MLB_SEARCH_PARAMS.copy()
  params.update(query)
  json = JSON.ObjectFromURL(MLB_URL_SEARCH + '?' + urllib.urlencode(params))
  del params

  if json['total'] < 1:
    return MessageContainer('No Results', 'No results were found.')
    # dir.SetMessage('No Results', 'No results were found.')

  else:
    for entry in json['mediaContent']:
      id = entry['mid']
      duration = HMSDurationToMilliseconds(entry['duration'])
      title = entry['blurb']
      desc = entry['bigBlurb']
      thumb = entry['thumbnails'][0]['src']

      try:
        dir.Append(_getHighlightVideoItem(id, title, desc, duration, thumb))
      except:
        pass

  return dir

####################################################################################################
def HMSDurationToMilliseconds(duration):
  duration = time.strptime(duration, '%H:%M:%S')
  return str(((duration[3]*60*60)+(duration[4]*60)+duration[5])*1000)

####################################################################################################
def findTeamById(id):
  for team in MLB_TEAMS:
    if team["id"] == str(id):
      return team
