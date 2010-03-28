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
  
