import re, sys, time, urllib
from PMS import Plugin, Log, DB, Thread, XML, HTTP, JSON, RSS, Utils
from PMS.MediaXML import MediaContainer, DirectoryItem, VideoItem, WebVideoItem, SearchDirectoryItem
from PMS.Shorthand import _L, _R

# plugin config

MLB_PLUGIN_PREFIX = '/video/mlb'

# mlb.com config

MLB_URL_ROOT   = 'http://mlb.mlb.com'

MLB_URL_MEDIA_ROOT = MLB_URL_ROOT + '/media'
MLB_URL_VIDEO_PAGE = MLB_URL_MEDIA_ROOT + '/video.jsp?mid='

# JSON media search (nice work, MLB :)
MLB_URL_SEARCH = MLB_URL_ROOT + '/ws/search/MediaSearchService?type=json&start=1&hitsPerPage=12&ns=1&text='

# XML files
MLB_URL_XML_ROOT       = MLB_URL_ROOT + '/gen'
MLB_URL_GAME_DETAIL    = MLB_URL_XML_ROOT + '/multimedia/detail/%s/%s/%s/%s.xml'
MLB_URL_MEDIA_XML_ROOT = MLB_URL_XML_ROOT + '/mlb/components/multimedia'
MLB_URL_TOP_VIDEOS     = MLB_URL_MEDIA_XML_ROOT + '/topvideos.xml'
MLB_URL_TOP_SEARCHES   = MLB_URL_MEDIA_XML_ROOT + '/keyword_links.xml'

MLB_TEAMS = [
  'Arizona Diamondbacks', 'Atlanta Braves', 'Baltimore Orioles',
  'Boston Red Sox', 'Chicago Cubs', 'Chicago White Sox',
  'Cincinnati Reds', 'Cleveland Indians', 'Colorado Rockies',
  'Detroit Tigers', 'Florida Marlins', 'Houston Astros',
  'Kansas City Royals', 'Los Angeles Angels of Anaheim', 'Los Angeles Dodgers',
  'Milwaukee Brewers', 'Minnesota Twins', 'New York Mets',
  'New York Yankees', 'Oakland Athletics', 'Philadelphia Phillies',
  'Pittsburgh Pirates', 'San Diego Padres', 'San Francisco Giants',
  'Seattle Mariners', 'St. Louis Cardinals', 'Tampa Bay Rays',
  'Texas Rangers', 'Toronto Blue Jays', 'Washington Nationals'
]

####################################################################################################
def Start():
  Plugin.AddRequestHandler(MLB_PLUGIN_PREFIX, HandleVideosRequest, "MLB", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("Details", viewMode="InfoList", contentType="items")
####################################################################################################

def HMSDurationToMilliseconds(duration):
  duration = time.strptime(duration, '%H:%M:%S')
  return str(((duration[3]*60*60)+(duration[4]*60)+duration[5])*1000)

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

def populateFromSearch(query, dir):
  dir.SetViewGroup('Details')

  json = JSON.DictFromURL(MLB_URL_SEARCH + urllib.quote(query))

  if json['total'] < 1:
    dir.SetMessage('No Results', 'Nothing found searching for: ' + query)

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

  # Top level menu
  if depth == 0:
    dir.AppendItem(DirectoryItem('featured', 'Featured Highlights'))
    dir.AppendItem(DirectoryItem('teams',    'Team Highlights'))
    dir.AppendItem(DirectoryItem('popular',  'Popular Searches'))
    dir.AppendItem(SearchDirectoryItem('search',  'Search', 'Enter some search terms'))

  # Featured videos
  elif path == 'featured':
    dir.SetAttr('title2', 'Featured')
    dir = populateFromXML(MLB_URL_TOP_VIDEOS, dir)

  # Team list
  elif path == 'teams':
    dir.SetAttr('title2', 'Teams')
    for team in MLB_TEAMS:
      dir.AppendItem(DirectoryItem(team, team))

  # Popular searches
  elif path == 'popular':
    dir.SetAttr('title2', 'Popular')
    dir = populateFromXML(MLB_URL_TOP_SEARCHES, dir, True)

  # A team's video list, or list of videos with a keyword from the popular list
  elif path.startswith('teams/') or path.startswith('popular/'):
    dir.SetAttr('title2', pathNouns[-1])
    dir = populateFromSearch('"' + pathNouns[-1] + '"', dir)

  # Search for a keyword and list results
  elif path.startswith('search/'):
    query = pathNouns[-1]
    dir.SetAttr('title2', query)
    dir = populateFromSearch(query, dir)

  return dir.ToXML()
