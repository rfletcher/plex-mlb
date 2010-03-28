# plex
from PMS import Prefs

# plugin
from Code.Classes.Team import Team
from Code.Config import C

teams = []
for team in C["TEAMS"]:
  teams.append(Team(team))

############################################################################
def favoriteTeam():
  return findByFullName(Prefs.Get('team'))

############################################################################
def findByFullName(fullName):
  for team in teams:
    if team.fullName() == fullName:
      return team

############################################################################
def findById(id):
  for team in teams:
    if str(team.id) == str(id):
      return team

############################################################################
def toOptions():
  options = teams[:]
  options.reverse()
  
  values = '(None)|'
  for team in options:
    values += team.fullName() + '|'
  del options
  
  return values

