# system
import isodate
import re
import urllib

# plex
from PMS import JSON, Prefs, XML
from PMS.Objects import DirectoryItem, Function, InputDirectoryItem, \
                        MediaContainer, PrefsItem, RTMPVideoItem, VideoItem, \
                        WebVideoItem
from PMS.Shortcuts import R

# plugin
from Code import Util
from Code.Config import C
from Code.Classes import Game, TeamList

def MenuHandler(sender, cls=None, **kwargs):
  """
  A menu class factory.  The Plex Function() wrapper doesn't seem to like classes as arguments.
  TODO: I'm not convinced that this function is necessary. Investigate further.
  """
  return cls(sender, **kwargs)
  

class ABCMenu(MediaContainer):
  """
  Abstract Menu base class.
  """
  def __init__(self, **kwargs):
    """
    Initialize a Menu.  Child classes must call ABCMenu.__init__()
    """
    defaults = {
      'art': R('art-default.jpg'),
      'title1': C["PLUGIN_NAME"],
      'viewGroup': "List"
    }
    defaults.update(**kwargs)
    
    MediaContainer.__init__(self, **defaults)
  
  def AddMenu(self, menuClass, title, menuargs={}, **kwargs):
    """
    Add a menu item which opens a submenu.
    """
    self.Append(Function(DirectoryItem(MenuHandler, title, **menuargs), cls=menuClass, **kwargs))
  
  def AddPopupMenu(self, menuClass, title, menuargs={}, **kwargs):
    """
    Add a menu item which opens as a popup
    """
    menuargs.update(popup=True)
    Util.dump(menuargs)
    self.AddMenu(menuClass, title, menuargs, **kwargs)
  
  def AddPreferences(self, title="Preferences"):
    """
    Add a menu item which opens the preferences dialog.
    """
    self.Append(PrefsItem(title))
  
  def AddSearch(self, menuClass, title="Search", message=None, **kwargs):
    """
    Add a menu item which opens a search dialog.
    """
    message = message if message is not None else title
    self.Append(Function(InputDirectoryItem(MenuHandler, title, message, thumb=R("search.png")), cls=menuClass, **kwargs))
  
  def AddMessage(self, message, title=C['PLUGIN_NAME']):
    """
    Add a menu item which opens a message dialog.
    """
    self.AddMenu(Message, title, message=message)
  
  def ShowMessage(self, message, title=C['PLUGIN_NAME']):
    """
    Show a message immediately.
    """
    MediaContainer.__init__(self, header=title, message=message)
  

class ABCHighlightsListMenu(ABCMenu):
  """
  Abstract menu for a list of highlights videos
  """  
  def getVideoItem(self, id, url=None, title=None, subtitle=None, summary=None, duration=None, thumb=None):
    """
    Get the VideoItem for a highlight video, either by assembling the data we
    already have, for fetching more from mlb.com
    """
    # (year, month, day, content_id) = (id[:4], id[4:6], id[6:8], id[8:])
    # subtitle = None #"posted %s/%s/%s" % (month, day, year)
    xml = None
    
    if None in [url, title, subtitle, summary, duration, thumb]:
      xurl = C["URL"]["GAME_DETAIL"] % (id[-3], id[-2], id[-1], id)
      xml = XML.ElementFromURL(xurl, headers={"Referer": Util.getURLRoot(xurl)})
    
    if url is None:
      # TODO this seems fragile.  investigate another way.
      for scenario in [
        "FLASH_1000K_640X360",
        "MLB_FLASH_1000K_PROGDNLD",
        "MLB_FLASH_1000K_STREAM_VPP",
        "FLASH_800K_640X360",
        "MLB_FLASH_800K_PROGDNLD",
        "MLB_FLASH_800K_STREAM_VPP",
        "FLASH_400K_600X338"
      ]:
        url = Util.XPathSelectOne(xml, 'url[@playback_scenario="' + scenario + '"]')
        if url is not None:
          break
      else:
        # couldn't find a URL
        return
    
    if duration is None:
      duration_string = Util.XPathSelectOne(xml, 'duration')
      if duration_string is not None:
        duration = int(Util.parseDuration(duration_string)) * 1000
    if title is None:
      title = Util.XPathSelectOne(xml, 'headline')
    if subtitle is None:
      date = isodate.parse_datetime(Util.XPathSelectOne(xml, '//@date'))
      # Log(date.astimezone(datetime.datetime.now().tzinfo))
      # subtitle = date.strftime("%a, %d %b %Y %H:%M:%S %Z")
      subtitle = date.strftime("%A, %B %d")
    
    if summary is None:
      summary = re.sub("^\s*(\d+\.){2}\d+\:", "", str(Util.XPathSelectOne(xml, 'big-blurb')))
    if thumb is None:
      thumb = Util.XPathSelectOne(xml, 'thumbnailScenarios/thumbnailScenario[@type="3"]')
    
    if url[:7] == "rtmp://":
      # pass clip as an empty string to prevent an exception
      return RTMPVideoItem(url, clip="", title=title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)
    else:
      return VideoItem(url, title, subtitle=subtitle, summary=summary, duration=duration, thumb=thumb)
  

class Message(ABCMenu):
  """
  A Menu which displays a message.
  """
  def __init__(self, sender, message=None, **kwargs):
    ABCMenu.__init__(self)
    self.ShowMessage(message, **kwargs)
  

class MainMenu(ABCMenu):
  """
  The top-level menu
  """
  def __init__(self):
    """
    Initialize the menu with menu items.
    """
    ABCMenu.__init__(self)
    self.AddMenu(DailyGameMenu, "Today's Games", date=Util.TimeEastern())
    self.AddMenu(HighlightsMenu, 'Highlights')
    self.AddPreferences()
  

class DailyGameMenu(ABCMenu):
  """
  A list of games for a given day.
  """
  def __init__(self, sender, date=Util.TimeEastern()):
    """
    Fetch the list of games for this day from mlb.com, adding each to the menu.
    """
    ABCMenu.__init__(self, title2=sender.itemTitle, viewGroup='Details')
    
    # only pull the media list if the preference that needs it is in play
    streams = {}
    # if teams.findByFullName(Prefs.Get('team')) != None:
    #   streams = _MediaStreams()
    
    items = []
    # load the game list from the populated url
    for xml in XML.ElementFromURL(Util.DateURL(date, C["URL"]["GAMES"]), cacheTime=C["GAME_CACHE_TTL"]).xpath('game'):
      game = Game.fromXML(xml)
      if streams: game.streams = streams[game.event_id]
      
      item = {
        'game': game,
        'video_url': C["URL"]["PLAYER"] + "?" + urllib.urlencode({
          'calendar_event_id': game.event_id,
          'content_id': game.getContentID(),
          'source': 'MLB'
        })
      }
      items.append(item)
    
    # move favorite team's game(s) to the top
    for i, item in enumerate(items):
      if item['game'].home_team.isFavorite() or item['game'].away_team.isFavorite():
        items.insert(0, items.pop(i))
    
    # add the games as menu items
    for item in items:
      try:
        self.Append(WebVideoItem(item['video_url'], item['game'].getMenuLabel(), subtitle=item['game'].getSubtitle(), summary=item['game'].getDescription(), thumb=R('icon-video-default.png')))
      except KeyError:
        Log('no video: ' + item['game'].getMenuLabel())
        self.Append(MessageItem(item['game'].getMenuLabel(), "No Video", "There is no video available for this game.",  subtitle=item['game'].getSubtitle(), summary=item['game'].getDescription()))
  

class FeaturedHighlightsMenu(ABCHighlightsListMenu):
  """
  The highlights/featured Menu
  """
  def __init__(self, sender):
    """
    Fetch a list of featured highlights from mlb.com, adding each to the menu.
    """
    ABCMenu.__init__(self, title2=sender.itemTitle, viewGroup="Details")
    for entry in XML.ElementFromURL(C["URL"]["TOP_VIDEOS"]).xpath('item'):
      id = entry.get("content_id")
      title = Util.XPathSelectOne(entry, "title")
      summary = Util.XPathSelectOne(entry, "big_blurb")
      duration = int(Util.parseDuration(Util.XPathSelectOne(entry, "duration"))) * 1000
      thumb = Util.XPathSelectOne(entry, "pictures/picture[@type='dam-raw-thumb']/url")
      url = Util.XPathSelectOne(entry, "url[@speed=1000]")
      
      self.Append(self.getVideoItem(id, url=url, title=title, summary=summary, duration=duration, thumb=thumb))
  

class HighlightsMenu(ABCMenu):
  """
  The highlights/ Menu
  """
  def __init__(self, sender):
    ABCMenu.__init__(self, title2=sender.itemTitle)
    self.AddMenu(FeaturedHighlightsMenu, 'Featured Highlights')
    self.AddMenu(TeamListMenu, 'Team Highlights', submenu=HighlightsSearchMenu)
    self.AddMenu(HighlightsSearchMenu, 'MLB.com FastCast', query='FastCast')
    self.AddMenu(HighlightsSearchMenu, 'MLB Network')
    self.AddMenu(HighlightsSearchMenu, 'Plays of the Day')
    self.AddSearch(HighlightsSearchMenu, title='Search Highlights')
  

class HighlightsSearchMenu(ABCHighlightsListMenu):
  """
  A Menu of highlights search results.
  """
  def __init__(self, sender, teamId=None, query=None):
    """
    Search mlb.com highlights for either a query, or a team ID, adding each
    result to the menu.
    """
    ABCMenu.__init__(self, viewGroup='Details', title2=sender.itemTitle)
    
    params = C["SEARCH_PARAMS"].copy()
    if teamId is not None:
      params.update({"team_id": teamId})
    else:
      params.update({"text": query if query is not None else sender.itemTitle})
    
    url = C["URL"]["SEARCH"] + '?' + urllib.urlencode(params)
    json = JSON.ObjectFromURL(url, headers={"Referer": Util.getURLRoot(url)})
    
    if json['total'] < 1:
      self.ShowMessage('No results were found.', title='No Results')
    else:
      for entry in json['mediaContent']:
        self.Append(self.getVideoItem(entry['contentId']))
  

class TeamListMenu(ABCMenu):
  """
  A Menu consisting of a list of teams.
  """
  def __init__(self, sender, submenu=None):
    """
    List teams, displaying the 'submenu' Menu when selected.
    """
    ABCMenu.__init__(self, title2=sender.itemTitle)
    
    favoriteteam = TeamList.findByFullName(Prefs.Get('team'))
    if favoriteteam:
      self.AddMenu(submenu, C["FAVORITE_MARKER"] + favoriteteam.fullName(), teamId=favoriteteam.id)
    
    for team in TeamList.teams:
      if not favoriteteam or favoriteteam != team:
        self.AddMenu(submenu, team.fullName(), teamId=team.id)
  
