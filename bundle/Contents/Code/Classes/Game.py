# system
from copy import deepcopy
import re
import time

# plex
from PMS import Prefs

# plugin
from Code import Util
from Code.Classes import TeamList
from Code.Config import C

##############################################################################
class Game:
  def __init__(self):
    self.home_team = None
    self.away_team = None
    self.event_id = None
    self.status = {
      "indicator": None, "label": None, "reason": None, "inning": None, "half": None
    }
    self.streams = {}
    self.situation = {
      "baserunners": None, "outs": None
    }
    self.home_line = {
      "innings": [], "runs": None, "hits": None, "errors": None
    }
    self.away_line = deepcopy(self.home_line)
    self.players = {
      "pitcher": None, "batter": None, "winning_pitcher": None, "losing_pitcher": None, "save_pitcher": None
    }
    self.time = None
    # self.xml = None
  
  ############################################################################
  def getDescription(self):
    # status codes, by category
    #   prior to start:
    #     S  = scheduled
    #     PR = pregame, rain (delayed start)
    #     PW = pre-game warmup
    #     P  = pregame
    #   in-game:
    #     I  = in-progress
    #     IR = in-progress, rain? (have seen this for a delayed start)
    #     DA = delayed action? (in-game delay)
    #   post-game:
    #     FR = final, rain (called early)
    #     DR = delayed, rescheduled (postponed)
    #     O  = game over (but stats are not yet official, so not "final")
    #     F  = final
    
    if self.isScheduled():
      if 'home_probable_pitcher' not in self.players or \
         'away_probable_pitcher' not in self.players:
        return ""
      
      home_starter = self.players['home_probable_pitcher']
      away_starter = self.players['away_probable_pitcher']
      
      return "\n".join([
        "%s: %s (%s-%s, %s ERA)" % (self.away_team.abbrev, away_starter['name'], away_starter['wins'], away_starter['losses'], away_starter['era']),
        "%s: %s (%s-%s, %s ERA)" % (self.home_team.abbrev, home_starter['name'], home_starter['wins'], home_starter['losses'], home_starter['era'])
      ])
    
    # in progress
    elif self.isInProgress():
      if not Prefs.Get('allowspoilers'):
        return None
      
      batter = self.players['batter']
      pitcher = self.players['pitcher']
      
      if self.status['half'] == 'top':
        batter_team = self.away_team
        pitcher_team = self.home_team
      else:
        batter_team = self.home_team
        pitcher_team = self.away_team
      
      return self.getScore() + "\n".join([
        "At Bat (%s):" % (batter_team.abbrev),
        "\t\t\t\t%s (%s for %s)" % (batter['name'], batter['h'], batter['ab']),
        "\t\t\t\tSeason: %s AVG., %s RBI, %s HR" % (batter['avg'], batter['rbi'], batter['hr']),
        "",
        "Pitching (%s):" % (pitcher_team.abbrev),
        "\t\t\t\t%s (%s IP, %s ER)" % (pitcher['name'], pitcher['ip'], pitcher['er']),
        "\t\t\t\tSeason: %s-%s, %s ERA" % (pitcher['wins'], pitcher['losses'], pitcher['era']),
        "",
        "%s on base, %s out" % (self.situation['baserunners'], self.situation['outs'])
      ])
    
    # final
    elif self.isFinal():
      if not Prefs.Get('allowspoilers'):
        return None
      
      wpitcher = self.players['winning_pitcher']
      lpitcher = self.players['losing_pitcher']
      spitcher = self.players['save_pitcher']
      
      description = self.getScore() + "\n".join([
        "Win: %s (%s-%s, %s)" % (wpitcher['name'], wpitcher['wins'], wpitcher['losses'], wpitcher['era']),
        "Loss: %s (%s-%s, %s)" % (lpitcher['name'], lpitcher['wins'], lpitcher['losses'], lpitcher['era'])
      ])
      
      if spitcher:
        description += ("\nSave: %s (%s)" % (spitcher['name'], spitcher['saves']))
      
      return description
    
    # unhandled
    return None
  
  ############################################################################
  def getContentID(self):
    if self.streams:
      if self.home_team.isFavorite():
        return self.streams['video_home']['id']
      elif self.away_team.isFavorite():
        return self.streams['video_away']['id']
      
    return ''
  
  ############################################################################
  def getScore(self):
    if self.home_line['runs'] and self.away_line['runs']:
      if int(self.home_line['runs']) > int(self.away_line['runs']):
        return "%s %s, %s %s\n\n" % (self.home_team.name, self.home_line['runs'], self.away_team.name, self.away_line['runs'])
      else:
        return "%s %s, %s %s\n\n" % (self.away_team.name, self.away_line['runs'], self.home_team.name, self.home_line['runs'])
  
  ############################################################################
  def getSubtitle(self):
    # scheduled
    if self.status['indicator'] == 'S':
      return self.time
    
    # in progress
    elif self.status['indicator'] == 'I':
      status = 'In Progress'
      if Prefs.Get('allowspoilers'):
        status += ", %s %s" % (self.status['half'], self.status['inning'])
      return status
    
    # delayed, postponed
    elif self.status['indicator'] in [ 'DR', 'DA', 'IR', 'PR' ]:
      return "%s: %s" % (self.status['label'], self.status['reason'])
    
    # final
    elif self.status['indicator'] in [ 'O', 'F', 'FR' ]:
      status = self.status['label']
      if Prefs.Get('allowspoilers') and int(self.status['inning']) != 9:
        status += ", %s innings" % self.status['inning']
      return status
    
    # unknown, unhandled (P = pregame, W = warmup)
    else:
      return self.status['label']
  
  ############################################################################
  def getMenuLabel(self):
    if not self.home_team or not self.away_team:
      return ""
    else:
      return "%s%s @ %s%s" % (
        C["FAVORITE_MARKER"] if self.away_team.isFavorite() else "",
        self.away_team.name,
        C["FAVORITE_MARKER"] if self.home_team.isFavorite() else "",
        self.home_team.name
      )
  
  ############################################################################
  def getTime(self):
    timestr = re.sub(r" [^\\s]+$", "", self.time)
    try:
      return time.strptime(timestr, "%I:%M%p")
    except:
      return None
  
  ############################################################################
  def isFavorite(self):
    return self.home_team.isFavorite() or self.away_team.isFavorite()
  
  ############################################################################
  def isFinal(self):
    return self.status['indicator'] in [ 'F', 'O', 'FR' ]
  
  ############################################################################
  def isInProgress(self):
    return self.status['indicator'] == 'I'

  ############################################################################
  def isScheduled(self):
    return self.status['indicator'] in ['S', 'PW', 'PR', 'P']

##############################################################################
def fromXML(xml):
  game = Game()
  
  # exhibition games not supported
  if Util.XPathSelectOne(xml, "./@game_type") == "E":
    return
  
  game.home_team = TeamList.findById(Util.XPathSelectOne(xml,"./@home_team_id"))
  game.away_team = TeamList.findById(Util.XPathSelectOne(xml,"./@away_team_id"))
  
  game.event_id = Util.XPathSelectOne(xml,"game_media/media/@calendar_event_id")
  game.time = Util.XPathSelectOne(xml, "./@time") + ("AM" if Util.XPathSelectOne(xml, "./@ampm").upper() == "AM" else "PM") + " " + Util.XPathSelectOne(xml, "./@time_zone")
  
  game.status.update({
    "indicator": Util.XPathSelectOne(xml,"status/@ind"),
    "label": Util.XPathSelectOne(xml,"status/@status"),
    "reason": Util.XPathSelectOne(xml,"status/@reason"),
    "inning": Util.XPathSelectOne(xml,"status/@inning"),
    "half": ("top" if Util.XPathSelectOne(xml,"status/@top_inning") == "Y" else "bot")
  })
  
  on_base = Util.XPathSelectOne(xml, "runners_on_base/@status") or 0
  game.situation.update({
    # on base status is a bitfield.  count how many of the first 3 bits are set.
    "baserunners": sum([((int(on_base) & 7) >> bit) & 1 for bit in range(3)]),
    "outs": Util.XPathSelectOne(xml,"./@o")
  })
  
  for inning in xml.xpath('linescore/inning'):
    game.home_line["innings"] += (Util.XPathSelectOne(inning, "./@home") or "")
    game.away_line["innings"] += (Util.XPathSelectOne(inning, "./@away") or "")
  for stat in ["runs", "hits", "errors"]:
    game.home_line[stat] = Util.XPathSelectOne(xml,"linescore/" + stat[0] + "/@home")
    game.away_line[stat] = Util.XPathSelectOne(xml,"linescore/" + stat[0] + "/@away")
  
  for player, stats in [
    ["home_probable_pitcher", ["era", "wins", "losses"]],
    ["away_probable_pitcher", ["era", "wins", "losses"]],
    ["batter", ["h", "ab", "avg", "rbi", "hr"]],
    ["pitcher", ["ip", "er", "wins", "losses", "era"]],
    ["winning_pitcher", ["era", "wins", "losses"]],
    ["losing_pitcher", ["era", "wins", "losses"]],
    ["save_pitcher", ["era", "wins", "losses", "saves"]]
  ]:
    if Util.XPathSelectOne(xml, player + '/@id'):
      game.players[player] = {
        "name": Util.XPathSelectOne(xml, player + '/@first') + " " + Util.XPathSelectOne(xml, player + '/@last')
      }
      for stat in stats:
        game.players[player][stat] = Util.XPathSelectOne(xml, player + '/@' + stat)
  
  return game
  
