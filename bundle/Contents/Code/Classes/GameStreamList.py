class GameStreamList(list):
  """
  A list of Streams for a given game
  """
  def __init__(self, streams, game=None):
    """
    Iniialize the stream list with a list of Stream objects
    """
    self.game = game
    self.extend(streams)
    self.sort(compare)
  
  def getBest(self):
    """
    Find the best stream in the list
    """
    best = None
    priority = [None, 'audio', 'away', 'basic', 'national', 'home', None, None, None, 'video']
    
    for stream in self:
      weight = 0
      if stream.type == 'home' and self.game.home_team.isFavorite() or \
         stream.type == 'away' and self.game.away_team.isFavorite():
        weight += 4
      try:
        weight += priority.index(stream.type)
        weight += priority.index(stream.kind)
      except: pass
      if not best or weight > best['weight']:
        best = {'stream': stream, 'weight': weight}
    
    return best['stream']

def compare(a, b, field=0):
  fields = ['national', 'away', 'home', 'video', 'audio', 'basic', 'condensed', 'highlights']
  field_val = fields[field]
  
  # move favorite team's game(s) to the top
  if field_val in ['home', 'away', 'national', 'basic']:
    prop = 'type'
  elif field_val in ['video', 'audio', 'condensed', 'highlights']:
    prop = 'kind'
  
  if ((getattr(a, prop) == field_val and getattr(b, prop) == field_val) or \
     (getattr(a, prop) != field_val and getattr(b, prop) != field_val)) and \
     (field < len(fields) - 1):
    return compare(a, b, field + 1)
  if getattr(a, prop) == field_val:
    return -1
  if getattr(b, prop) == field_val:
    return 1
  
  return 0
  
