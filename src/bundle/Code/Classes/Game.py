from copy import deepcopy
from .. import Util, Config
from PMS import Log, Prefs

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
    # in progress
    if self.status['indicator'] == 'I':
      if Prefs.Get('allowspoilers') == 'false':
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
        "\t\t\t\tSeason: %s-%s, %s ERA" % (pitcher['wins'], pitcher['losses'], pitcher['era'])
      ])

    # final
    elif self.status['indicator'] == 'F' or self.status['indicator'] == 'O':
      if Prefs.Get('allowspoilers') == 'false':
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
      status = 'In Progress, %s %s' % (
        self.status['half'], self.status['inning'],
      )

      if Prefs.Get('allowspoilers') == 'false':
        return status
      else:
        return status + ' (%s on, %s out)' % (
          self.situation['baserunners'], self.situation['outs']
        )

    # delayed, postponed
    elif self.status['indicator'] == 'DR' or self.status['indicator'] == 'DA':
      return "%s: %s" % (self.status['label'], self.status['reason'])

    # final (over)
    elif self.status['indicator'] == 'O' or self.status['indicator'] == 'F':
      status = self.status['label']
      if int(self.status['inning']) != 9:
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
        Config.FAVORITE_MARKER if self.away_team.isFavorite() else "",
        self.away_team.name,
        Config.FAVORITE_MARKER if self.home_team.isFavorite() else "",
        self.home_team.name
      )

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

  on_base = Util.XPathSelectOne(xml, "runners_on_base/@status") or 0
  game.situation.update({
    # on base status is a bitfield.  count how many of the first 3 bits are set.
    "baserunners": sum([((int(on_base) & 7) >> bit) & 1 for bit in range(3)]),
    "outs": Util.XPathSelectOne(xml,"./@o")
  })

  for inning in xml.xpath('linescore/inning'):
    game.home_line["innings"] += Util.XPathSelectOne(inning, "./@home")
    game.away_line["innings"] += Util.XPathSelectOne(inning, "./@away")
  for stat in ["runs", "hits", "errors"]:
    game.home_line[stat] = Util.XPathSelectOne(xml,"linescore/" + stat[0] + "/@home")
    game.away_line[stat] = Util.XPathSelectOne(xml,"linescore/" + stat[0] + "/@away")

  for player, stats in [
    ["batter", ["h", "ab", "avg", "rbi", "hr"]],
    ["pitcher", ["ip", "er", "wins", "losses", "era"]],
    ["winning_pitcher", ["era", "wins", "losses"]],
    ["losing_pitcher", ["era", "wins", "losses"]],
    ["save_pitcher", ["era", "wins", "losses", "saves"]]
  ]:
    if Util.XPathSelectOne(xml, player) and Util.XPathSelectOne(xml, player + '/@id'):
      game.players[player] = {
        "name": Util.XPathSelectOne(xml, player + '/@first') + " " + Util.XPathSelectOne(xml, player + '/@last')
      }

      for stat in stats:
        game.players[player][stat] = Util.XPathSelectOne(xml, player + '/@' + stat)

  return game