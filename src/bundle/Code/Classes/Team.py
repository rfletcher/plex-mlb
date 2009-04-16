class Team:
  def __init__(self, teamObj=None, name=None, city=None, id=None):
    if teamObj:
      name = teamObj['name']
      id = teamObj['id']
      city = teamObj['city']

    self.id = id
    self.name = name
    self.city = city

  ############################################################################
  def fullName(self):
    return "%s %s" % (self.city, self.name)
