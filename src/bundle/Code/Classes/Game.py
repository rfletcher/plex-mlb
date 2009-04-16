from .. import Util
from PMS import Log

##############################################################################
class Game:
  def __init__(self):
    self.home_team = None
    self.away_team = None
    self.event_id = None
    self.status = {
      "indicator": None, "label": None, "reason": None, "inning": None, "half": None
    }
    self.situation = {
      "baserunners": None, "outs": None, "pitcher": None, "batter": None
    }
    self.time = None
    # self.xml = None

  ############################################################################
  def getDescription(self):
    # in progress
    if self.status['indicator'] == 'I':
      batter_info = self.situation['batter']
      pitcher_info = self.situation['pitcher']

      if self.status['half'] == 'top':
        batter_team = self.away_team
        pitcher_team = self.home_team
      else:
        batter_team = self.home_team
        pitcher_team = self.away_team

      return "\n".join([
        "At Bat (%s):" % (batter_team.abbrev),
        "\t\t\t\t%s (%s for %s)" % (batter_info['name'], batter_info['h'], batter_info['ab']),
        "\t\t\t\tSeason: %s AVG., %s RBI, %s HR" % (batter_info['avg'], batter_info['rbi'], batter_info['hr']),
        "",
        "Pitching (%s):" % (pitcher_team.abbrev),
        "\t\t\t\t%s (%s IP, %s ER)" % (pitcher_info['name'], pitcher_info['ip'], pitcher_info['er']),
        "\t\t\t\tSeason: %s-%s, %s ERA" % (pitcher_info['wins'], pitcher_info['losses'], pitcher_info['era'])
      ])

    return ""

  ############################################################################
  def getSubtitle(self):
    # unhandled: P = pregame, W = warmup
    
    # scheduled
    if self.status['indicator'] == 'S':
      return self.time

    # in progress
    elif self.status['indicator'] == 'I':
      return 'In Progress, %s %s (%s on, %s out)' % (
        self.status['half'], self.status['inning'],
        self.situation['baserunners'], self.situation['outs']
      )

    # delayed, postponed
    elif self.status['indicator'] == 'DR' or\
         self.status['indicator'] == 'DA':
      return "%s: %s" % (self.status['label'], self.status['reason'])

    # final (over)
    elif self.status['indicator'] == 'O' or self.status['indicator'] == 'F':
      status = self.status['label']
      if int(self.status['inning']) != 9:
        status += ", %s innings" % self.status['inning']
      return status

    # unknown
    else:
      return self.status['label']

  ############################################################################
  def getMenuLabel(self):
    if not self.home_team or not self.away_team:
      return ""
    else:
      return "%s @ %s" % (self.away_team.name, self.home_team.name)

##############################################################################
def fromXML(xml, teams):
  game = Game()
  # game.xml = xml

  game.home_team = teams.findById(Util.XPathSelectOne(xml,"./@home_team_id"))
  game.away_team = teams.findById(Util.XPathSelectOne(xml,"./@away_team_id"))

  game.event_id = Util.XPathSelectOne(xml,"game_media/media/@calendar_event_id")
  game.time = Util.XPathSelectOne(xml, "./@time") + ("AM" if Util.XPathSelectOne(xml, "./@ampm").upper() == "AM" else "") + " " + Util.XPathSelectOne(xml, "./@time_zone")

  game.status.update({
    "indicator": Util.XPathSelectOne(xml,"status/@ind"),
    "label": Util.XPathSelectOne(xml,"status/@status"),
    "reason": Util.XPathSelectOne(xml,"status/@reason"),
    "inning": Util.XPathSelectOne(xml,"status/@inning"),
    "half": ("top" if Util.XPathSelectOne(xml,"status/@top_inning") == "Y" else "bot")
  })

  # Log('on base:' + Util.XPathSelectOne(xml, 'runners_on_base/@status'))
  # on base status is a bitfield: 1st = 1, 2nd = 2, 3rd = 4
  # 1 = 1st
  # 2 = 2nd
  # 3 = 1st/2nd
  # 4 = 3rd
  # 5 = 1st/3rd
  # 6 = 2nd/3rd
  # 7 = loaded!
  game.situation.update({
    "baserunners": 0,
    "batter": {},
    "outs": Util.XPathSelectOne(xml,"./@o"),
    "pitcher": {}
  })

  for player, stats in [['batter', ["h", "ab", "avg", "rbi", "hr"]], [ 'pitcher', ["ip", "er", "wins", "losses", "era"]]]:
    if Util.XPathSelectOne(xml, player):
      game.situation[player] = {
        "name": Util.XPathSelectOne(xml, player + '/@first') + " " + Util.XPathSelectOne(xml, player + '/@last')
      }

      for stat in stats:
        game.situation[player][stat] = Util.XPathSelectOne(xml, player + '/@' + stat)

  return game