from Code.Classes.Team import *

class TeamList(list):
  ############################################################################
  def __init__(self, teams):
    for team in teams:
      self.append(Team(team))
  
  ############################################################################
  def findByFullName(self, fullName):
    for team in self:
      if team.fullName() == fullName:
        return team
  
  ############################################################################
  def findById(self, id):
    for team in self:
      if str(team.id) == str(id):
        return team
  
  ############################################################################
  def toOptions(self):
    options = self[:]
    options.reverse()
    
    values = '(None)|'
    for team in options:
      values += team.fullName() + '|'
    del options
    
    return values
  
