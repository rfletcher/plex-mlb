# system
import datetime

# plex
from PMS import XML

# plugin
from Code import Util
from Code.Config import C
from Code.Classes import Game

class GameList(list):
  """
  A list of one day's games
  """
  def __init__(self, date, streams):
    """
    Load the list of games for a specific date from mlb.com
    """
    self.load(date, streams)
    self.sort()
  
  def load(self, date, streams):
    """
    Fetch game data from mlb.com and generate a list of Game objects
    """
    iphone_xml = XML.ElementFromURL(Util.DateURL(date, C["URL"]["GAMES"]), cacheTime=C["GAME_CACHE_TTL"])
    for xml in iphone_xml.xpath('game'):
      game = Game.fromXML(xml)
      game.streams = streams[game.event_id] if game.event_id else {}
      self.append(game)
    
    # move favorite team's game(s) to the top
    for i, game in enumerate(self):
      if game.home_team.isFavorite() or game.away_team.isFavorite():
        self.insert(0, self.pop(i))
  
