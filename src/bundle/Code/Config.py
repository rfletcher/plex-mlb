# plugin config

PLUGIN_PREFIX = '/video/mlb'

# mlb.com config

URL_ROOT   = 'http://mlb.mlb.com'

# JSON media search (nice work, MLB :)
URL_SEARCH = URL_ROOT + '/ws/search/MediaSearchService'
SEARCH_PARAMS = { "type" : "json", "start": 1, "hitsPerPage": 12, "ns": 1 }

# XML files
URL_GAME_DETAIL  = URL_ROOT + '/gen/multimedia/detail/%s/%s/%s/%s.xml'
URL_TOP_VIDEOS   = URL_ROOT + '/gen/mlb/components/multimedia/topvideos.xml'
URL_EPG_SERVICES = URL_ROOT + '/flash/mediaplayer/v4/RC5/xml/epg_services.xml'
URL_MLBTV_GAMES  = URL_ROOT + '/mobile/data/atbatScoreboard2009.jsp?y=%s&m=%s&d=%s'

# Teams
# TODO put these in a database
Teams = [
  { 'id': '109', 'abbrev': 'ARI', 'city': 'Arizona',       'name': 'Diamondbacks' },
  { 'id': '144', 'abbrev': 'ATL', 'city': 'Atlanta',       'name': 'Braves' },
  { 'id': '110', 'abbrev': 'BAL', 'city': 'Baltimore',     'name': 'Orioles' },
  { 'id': '111', 'abbrev': 'BOS', 'city': 'Boston',        'name': 'Red Sox' },
  { 'id': '112', 'abbrev': 'CHC', 'city': 'Chicago',       'name': 'Cubs' },
  { 'id': '145', 'abbrev': 'CWS', 'city': 'Chicago',       'name': 'White Sox' },
  { 'id': '113', 'abbrev': 'CIN', 'city': 'Cincinnati',    'name': 'Reds' },
  { 'id': '114', 'abbrev': 'CLE', 'city': 'Cleveland',     'name': 'Indians' },
  { 'id': '115', 'abbrev': 'COL', 'city': 'Colorado',      'name': 'Rockies' },
  { 'id': '116', 'abbrev': 'DET', 'city': 'Detroit',       'name': 'Tigers' },
  { 'id': '146', 'abbrev': 'FLA', 'city': 'Florida',       'name': 'Marlins' },
  { 'id': '117', 'abbrev': 'HOU', 'city': 'Houston',       'name': 'Astros' },
  { 'id': '118', 'abbrev': 'KC',  'city': 'Kansas City',   'name': 'Royals' },
  { 'id': '108', 'abbrev': 'LAA', 'city': 'Los Angeles',   'name': 'Angels' },
  { 'id': '119', 'abbrev': 'LAD', 'city': 'Los Angeles',   'name': 'Dodgers' },
  { 'id': '158', 'abbrev': 'MIL', 'city': 'Milwaukee',     'name': 'Brewers' },
  { 'id': '142', 'abbrev': 'MIN', 'city': 'Minnesota',     'name': 'Twins' },
  { 'id': '121', 'abbrev': 'NYM', 'city': 'New York',      'name': 'Mets' },
  { 'id': '147', 'abbrev': 'NYY', 'city': 'New York',      'name': 'Yankees' },
  { 'id': '133', 'abbrev': 'OAK', 'city': 'Oakland',       'name': 'Athletics' },
  { 'id': '143', 'abbrev': 'PHI', 'city': 'Philadelphia',  'name': 'Phillies' },
  { 'id': '134', 'abbrev': 'PIT', 'city': 'Pittsburgh',    'name': 'Pirates' },
  { 'id': '135', 'abbrev': 'SD',  'city': 'San Diego',     'name': 'Padres' },
  { 'id': '137', 'abbrev': 'SF',  'city': 'San Francisco', 'name': 'Giants' },
  { 'id': '136', 'abbrev': 'SEA', 'city': 'Seattle',       'name': 'Mariners' },
  { 'id': '138', 'abbrev': 'STL', 'city': 'St. Louis',     'name': 'Cardinals' },
  { 'id': '139', 'abbrev': 'TB',  'city': 'Tampa Bay',     'name': 'Rays' },
  { 'id': '140', 'abbrev': 'TEX', 'city': 'Texas',         'name': 'Rangers' },
  { 'id': '141', 'abbrev': 'TOR', 'city': 'Toronto',       'name': 'Blue Jays' },
  { 'id': '120', 'abbrev': 'WSH', 'city': 'Washington',    'name': 'Nationals' }
]
