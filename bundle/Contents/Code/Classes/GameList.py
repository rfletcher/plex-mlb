# system
import datetime

# plex
from PMS import XML

# plugin
from Code import Util
from Code.Config import C
from Code.Classes import Game, Stream
from Code.Classes.GameStreamList import GameStreamList

class GameList(list):
  """
  A list of one day's games
  """
  def __init__(self, date):
    """
    Load the list of games for a specific date from mlb.com
    """
    self.load(date)
    self.sort(compare)
  
  def load(self, date):
    """
    Fetch game data from mlb.com and generate a list of Game objects
    """
    streams = self.loadStreams(date)
    iphone_xml = XML.ElementFromURL(Util.DateURL(date, C["URL"]["GAMES"]), cacheTime=C["GAME_CACHE_TTL"], isHTML=True)
    # for some reason switching to the soup parser (isHTML=True) made every game
    # appear twice.  keep track of which games we've already listed.
    games_parsed = {}
    for xml in iphone_xml.xpath('game'):
      game = Game.fromXML(xml)
      if game:
        try: pseudo_id = game.home_team.fullName() + game.away_team.fullName()
        except: pseudo_id = None
        if pseudo_id in games_parsed:
          continue
        games_parsed[pseudo_id] = True
        
        if game.event_id:
          game.streams = streams[game.event_id]
          game.streams.game = game
        else:
          game.streams = {}
        self.append(game)
  
  def loadStreams(self, date):
    """
    Load stream data for a given day.  (A stream, for this purpose, is any
    game-specific media listed on http://mlb.mlb.com/mediacenter/)
    """
    events = {}
    table = XML.ElementFromURL(Util.DateURL(date, C["URL"]["MEDIA"]), True, encoding='UTF-8').cssselect('.mmg_table tbody')[0]
    
    # how many columns in the table?
    num_columns = 0
    for cell in table.cssselect('tr:first-child td'):
      num_columns += 1 if not cell.get('colspan') else int(cell.get('colspan'))

    for column_types in C["MEDIA_COLUMNS"]:
      if num_columns == len(column_types):
        # parse some HTML
        for row in table.cssselect('tr'):
          event_id = row.get('id')
          if not event_id: continue
          
          streams = []
          cells = row.cssselect('td')
          if len(cells) < len(column_types): continue
          
          for i in range(0, len(column_types)):
            stream = Stream.fromHTML(column_types[i], cells[i])
            if stream:
              streams.append(stream)
          
          events[event_id] = GameStreamList(streams)
        break
    
    return events
  


def compare(a, b):
  """
  Sort the game list in the same fashion as mlb.com (by start time, with
  complete games at the bottom).  Additionally, move favorite team's game(s) to
  the top.
  """
  comparisons = [
    [b.isFavorite(), a.isFavorite()],
    [b.isInProgress(), a.isInProgress()],
    [b.isScheduled(), a.isScheduled()],
    [a.getTime(), b.getTime()]
  ]
  
  for values in comparisons:
    cmpval = cmp(values[0], values[1])
    if cmpval != 0:
      return cmpval
    
  return 0
  
