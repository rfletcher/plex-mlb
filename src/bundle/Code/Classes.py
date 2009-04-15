class Team:
  ############################################################################
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


class TeamList(list):
  ############################################################################
  def __init__(self, teams):
    for team in teams:
      self.append(Team(team))

  ############################################################################
  def findById(self, id):
    for team in self:
      if str(team.id) == str(id):
        return team

  ############################################################################
  def options(self):
    options = self[:]
    options.reverse()
    values = '(None)|'
    for team in options:
      values += team.fullName() + '|'
    del options

    return values
