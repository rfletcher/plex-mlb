# plex
from PMS import Prefs

class Team:
  def __init__(self, teamObj=None, abbrev=None, name=None, city=None, id=None):
    if teamObj:
      name = teamObj['name']
      id = teamObj['id']
      city = teamObj['city']
      abbrev = teamObj['abbrev']
    
    self.id = id
    self.name = name
    self.city = city
    self.abbrev = abbrev
  
  ############################################################################
  def fullName(self):
    return "%s %s" % (self.city, self.name)
  
  ############################################################################
  def isFavorite(self):
    return self.fullName() == Prefs.Get('team')
  
