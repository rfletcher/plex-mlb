class GameStreamList(list):
  """
  A list of Streams for a given game
  """
  def __init__(self, streams):
    """
    Iniialize the stream list with a list of Stream objects
    """
    self.extend(streams)
    # self.sort(compare)
  

def compare(a, b):
  """
  Sort the stream list
  """
  # sort by team, with home team at the top
  if a.time < b.time:
    return -1
  elif a.time > b.time:
    return 1

  return 0
