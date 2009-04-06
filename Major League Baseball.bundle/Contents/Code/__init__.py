import re, sys, time, urllib
from PMS import Plugin, Log, Prefs, DB, Thread, XML, HTTP, JSON, RSS, Utils
from PMS.MediaXML import MediaContainer, DirectoryItem, VideoItem, WebVideoItem, SearchDirectoryItem

# plugin config

MLB_PLUGIN_PREFIX = '/video/mlb'

# mlb.com config

MLB_URL_ROOT   = 'http://mlb.mlb.com'

MLB_URL_MEDIA_ROOT = MLB_URL_ROOT + '/media'
MLB_URL_VIDEO_PAGE = MLB_URL_MEDIA_ROOT + '/video.jsp?mid='

# JSON media search (nice work, MLB :)
MLB_URL_SEARCH = MLB_URL_ROOT + '/ws/search/MediaSearchService'
MLB_SEARCH_PARAMS = { "type" : "json", "start": 1, "hitsPerPage": 12, "ns": 1 }

# XML files
MLB_URL_XML_ROOT       = MLB_URL_ROOT + '/gen'
MLB_URL_GAME_DETAIL    = MLB_URL_XML_ROOT + '/multimedia/detail/%s/%s/%s/%s.xml'
MLB_URL_MEDIA_XML_ROOT = MLB_URL_XML_ROOT + '/mlb/components/multimedia'
MLB_URL_TOP_VIDEOS     = MLB_URL_MEDIA_XML_ROOT + '/topvideos.xml'

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
  Plugin.AddRequestHandler(MLB_PLUGIN_PREFIX, HandleVideosRequest, "Major League Baseball", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("Details", viewMode="InfoList", contentType="items")

####################################################################################################

def HMSDurationToMilliseconds(duration):
  duration = time.strptime(duration, '%H:%M:%S')
  return str(((duration[3]*60*60)+(duration[4]*60)+duration[5])*1000)

def findTeamById(id):
  for team in MLB_TEAMS:
    if team["id"] == str(id):
      return team

def getVideoItem(id, title, desc, duration, thumb):
  (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
  subtitle = "%s/%s/%s" % (month, day, year)

  # # to load the HTML page w/ flash player
  # url = MLB_URL_VIDEO_PAGE + id
  # VidItem = WebVideoItem(url, title, desc, duration, thumb)

  # To load FLV directly (no ads, more fragile)
  # MUST grab the URL from the details XML.  Building the URL string from the
  # date will yield and occasional 404.
  xml = XML.ElementFromURL(MLB_URL_GAME_DETAIL % (year, month, day, content_id))
  url = xml.xpath('//url[@playback_scenario="MLB_FLASH_800K_PROGDNLD"]')[0].text
  VidItem = VideoItem(url, title, desc, duration, thumb)

  if subtitle:
    VidItem.SetAttr('subtitle', subtitle)

  return VidItem

def listGames(dir):
  games_url = 'http://gdx.mlb.com/components/game/mlb/year_2009/month_04/day_05/epg.xml'

  for game in XML.ElementFromURL(games_url).xpath('game'):
    home_team = findTeamById(game.xpath('./@home_team_id')[0])
    away_team = findTeamById(game.xpath('./@away_team_id')[0])
    url = 'http://mlb.mlb.com/flash/mediaplayer/v4/RC9/MP4.jsp?calendar_event_id=' + game.xpath('game_media/media/@calendar_event_id')[0]

    dir.AppendItem(WebVideoItem(url, away_team['name'] + ' @ ' + home_team['name'], "ddescription", "", None))

  return dir

def listTeams(dir):
  dir.SetAttr('title2', 'Teams')

  favoriteteam = findTeamById(Prefs.Get('favoriteteam'))
  if favoriteteam:
    dir.AppendItem(DirectoryItem(favoriteteam["id"], u"\u2605 " + favoriteteam["city"] + ' ' + favoriteteam["name"]))

  for team in MLB_TEAMS:
    if not favoriteteam or favoriteteam != team:
      dir.AppendItem(DirectoryItem(team["id"], team["city"] + ' ' + team["name"]))

  return dir

def populateFromSearch(query, dir):
  dir.SetViewGroup('Details')

  params = MLB_SEARCH_PARAMS.copy()
  params.update(query)
  json = JSON.DictFromURL(MLB_URL_SEARCH + '?' + urllib.urlencode(params))
  del params

  if json['total'] < 1:
    dir.SetMessage('No Results', 'No results were found.')

  else:
    for entry in json['mediaContent']:
      id = entry['mid']
      duration = HMSDurationToMilliseconds(entry['duration'])
      title = entry['blurb']
      desc = entry['bigBlurb']
      thumb = entry['thumbnails'][0]['src']

      try:
        Item = getVideoItem(id, title, desc, duration, thumb)
        dir.AppendItem(Item)
      except:
        pass

  return dir

def populateFromXML(url, dir, keyword_list = False):
  for entry in XML.ElementFromURL(url).xpath('item'):
    if keyword_list:
      title = entry.xpath('title')[0].text
      dir.AppendItem(DirectoryItem(title, title))

    else:
      dir.SetViewGroup('Details')

      id = entry.get('cid')
      title = entry.xpath('title')[0].text
      desc = entry.xpath('big_blurb')[0].text
      duration = HMSDurationToMilliseconds(entry.xpath('duration')[0].text)
      thumb = entry.xpath("pictures/picture[@type='small-text-graphic']/url")[0].text

      try:
        Item = getVideoItem(id, title, desc, duration, thumb)
        dir.AppendItem(Item)
      except:
        pass

  return dir

####################################################################################################
def HandleVideosRequest(pathNouns, depth):
  dir = MediaContainer("art-default.jpg", None, "MLB")

  dir.SetAttr("content", "items")

  if depth > 0:
    path = '/'.join(pathNouns)
    Log.Add(path)

  # Top level menu
  if depth == 0:
    dir.AppendItem(DirectoryItem('highlights', 'Highlights'))
    dir.AppendItem(DirectoryItem('mlbtv', 'MLB.tv'))
    dir.AppendItem(DirectoryItem('prefs', 'Preferences'))

  elif path == 'highlights':
    dir.AppendItem(DirectoryItem('featured', 'Featured Highlights'))
    dir.AppendItem(DirectoryItem('teams',    'Team Highlights'))
    dir.AppendItem(SearchDirectoryItem('search', 'Search', 'Search Highlights', Plugin.ExposedResourcePath("search.png")))

  # Highlights
  elif path.startswith('highlights/'):
    if path == 'highlights/featured':
      dir.SetAttr('title2', 'Featured')
      dir = populateFromXML(MLB_URL_TOP_VIDEOS, dir)

    # Team list
    elif path == 'highlights/teams':
      dir = listTeams(dir)

    # A team's video list
    elif path.startswith('highlights/teams/'):
      team = findTeamById(pathNouns[-1])
      dir.SetAttr('title2', team["name"])
      dir = populateFromSearch({"team_id": team["id"]}, dir)

    # Search for a keyword and list results
    elif path.startswith('highlights/search/'):
      query = pathNouns[-1]
      dir.SetAttr('title2', query)
      dir = populateFromSearch({"text": query}, dir)

  elif path == 'mlbtv':
    dir = listGames(dir)

  elif path == 'prefs':
    dir.AppendItem(DirectoryItem('favoriteteam', 'Favorite Team'))
    dir.AppendItem(SearchDirectoryItem('login', 'MLB.com Login', 'Enter your mlb.com login'))
    dir.AppendItem(SearchDirectoryItem('password', 'MLB.com Password', 'Enter your mlb.com password'))

  # Preferences
  elif path.startswith('prefs/'):
    # Setting a preference
    if depth == 3:
      key = pathNouns[-2]
      value = pathNouns[-1]
      Prefs.Set(key, value)

      if key == 'favoriteteam':
        dir.SetMessage("Set Preference", "Favorite team set.")
      elif path.startswith('prefs/login'):
        dir.SetMessage("Set Preference", "MLB.com login set.")
      elif path.startswith('prefs/password'):
        dir.SetMessage("Set Preference", "MLB.com password set.")

    # Choose a team
    elif path.startswith('prefs/favoriteteam'):
      dir = listTeams(dir)

  return dir.ToXML()
