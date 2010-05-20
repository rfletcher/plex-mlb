# system
import re

# plugin
from Code import Util

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
    if self.kind in ['audio', 'video']:
      category = {
        'home': game.home_team.name,
        'away': game.away_team.name,
        'national': 'National',
        'basic': 'Basic',
      }[self.type]
      # TODO the menu shouldn't be available if there's no link in the table
      label = "Soon" if self.pending else self.label
      source = (" (%s)" % label) if (self.type in ['home', 'away'] or self.pending) else ""
      alt = " Alt." if self.alternate else ""
      return "%s%s %s%s" % (category, alt, self.kind.capitalize(), source)
    elif self.kind == 'condensed':
      return "Condensed Game"
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
  
  # highlights
  if stream_type == 'highlights':
    try: stream.pack_id = re.search(r"[?&]game_pk=([^&]+)", cell.cssselect('a')[0].get('href')).group(1)
    except: pass
  # condensed games
  if stream_type == 'condensed':
    try: stream.id = re.search(r"[?&]content_id=([^&]+)", cell.cssselect('a')[0].get('href')).group(1)
    except: pass
  
  return stream
