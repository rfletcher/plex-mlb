# plugin config

PLUGIN_PREFIX = '/video/mlb'

# mlb.com config

URL_ROOT   = 'http://mlb.mlb.com'

# JSON media search (nice work, MLB :)
URL_SEARCH = URL_ROOT + '/ws/search/MediaSearchService'
SEARCH_PARAMS = { "type" : "json", "start": 1, "hitsPerPage": 12, "ns": 1 }

# XML files
URL_GAME_DETAIL = URL_ROOT + '/gen/multimedia/detail/%s/%s/%s/%s.xml'
URL_TOP_VIDEOS  = URL_ROOT + '/gen/mlb/components/multimedia/topvideos.xml'
URL_EPG_SERVICES = URL_ROOT + '/flash/mediaplayer/v4/RC5/xml/epg_services.xml'

# Teams
# TODO put these in a database
Teams = [
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
