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
    iphone_xml = XML.ElementFromURL(Util.DateURL(date, C["URL"]["GAMES"]), cacheTime=C["GAME_CACHE_TTL"])
    for xml in iphone_xml.xpath('game'):
      game = Game.fromXML(xml)
      if game:
        game.streams = streams[game.event_id] if game.event_id else {}
        self.append(game)
  
  def loadStreams(self, date):
    """
    Load stream data for a given day.  (A stream, for this purpose, is any
    game-specific media listed on http://mlb.mlb.com/mediacenter/)
    """
    table_columns = C["MEDIA_COLUMNS"]
    events = {}
    
    # parse some HTML
    for row in XML.ElementFromURL(Util.DateURL(date, C["URL"]["MEDIA"]), True, encoding='UTF-8').cssselect('.mmg_table tbody tr'):
      event_id = row.get('id')
      if not event_id: continue
      
      streams = []
      cells = row.cssselect('td')
      if len(cells) < len(table_columns): continue
      
      for i in range(0, len(table_columns)):
        stream = Stream.fromHTML(table_columns[i], cells[i])
        if stream:
          streams.append(stream)
      
      events[event_id] = GameStreamList(streams)
    
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
  
