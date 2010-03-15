# system
import re

# plugin
from Code import Util
# from Code.Classes import TeamList
# from Code.Config import C

##############################################################################
class Stream:
  def __init__(self):
    self.alternate = False # is this an alternate language stream?
    self.id = None # content id
    self.label = None # label (usually tv/radio call letters)
    self.pending = False
    self.kind = None # audio/video/highlights/condensed
    self.type = None # away/home/basic/national
    self.pack_id = None # for a "pack" of highlights
  
  def getMenuLabel(self, game):
    source = "(Not Yet Available)" if self.pending else self.label
    if self.kind in ['audio', 'video']:
      category = {
        'home': game.home_team.name,
        'away': game.away_team.name,
        'national': 'National',
        'basic': 'Basic',
      }[self.type]
      return "%s %s: %s" % (category, self.kind.capitalize(), source)
    else:
      return self.kind.capitalize()


def fromHTML(stream_type, cell):
  label = cell.text_content().strip()
  label = None if label == "" else label
  content_id = cell.get('id')
  
  if None in [stream_type, label]:
    return
  
  stream_type_regex = re.compile(r"^(?P<kind>[^_]+)(.*_(?P<type>[^_]+))?$")
  matches = stream_type_regex.match(stream_type).groupdict()

  stream = Stream();
  stream.id = content_id
  stream.kind = matches['kind']
  stream.alternate = True if "_alt_" in stream_type else False
  stream.type = matches['type']
  stream.label = None if label is "Watch" else label
  stream.pending = False if cell.cssselect('a') else True
  
  # for highlights
  # stream.game_pack = 
  if stream_type == 'highlights':
    try:
      stream.pack_id = re.search(r"[?&]game_pk=([^&]+)", cell.cssselect('a')[0].get('href')).group(1)
    except: pass
  
  return stream
