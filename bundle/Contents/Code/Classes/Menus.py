# system
import calendar
import datetime
import isodate
import pytz
import re
import urllib

# plex
from PMS import JSON, Prefs, XML
from PMS.Objects import DirectoryItem, Function, InputDirectoryItem, \
                        MediaContainer, PrefsItem, Redirect, RTMPVideoItem, \
                        VideoItem, WebVideoItem
from PMS.Shortcuts import R

# plugin
from Code import Util
from Code.Config import C
from Code.Classes import TeamList
from Code.Classes.GameList import GameList

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
      'title1': C["PLUGIN_NAME"] + ((" (" + str(C["PLUGIN_VERSION"]) + ")") if C["VERSION_IN_PLUGIN_NAME"] else ""),
      'viewGroup': "List"
    }
    defaults.update(**kwargs)
    
    MediaContainer.__init__(self, **defaults)
  
  def AddMenu(self, menuClass, label, menuargs={}, **kwargs):
    """
    Add a menu item which opens a submenu.
    """
    self.Append(Function(DirectoryItem(MenuHandler, label, **menuargs), cls=menuClass, **kwargs))
  
  def AddPopupMenu(self, menuClass, label, menuargs={}, **kwargs):
    """
    Add a menu item which opens as a popup
    """
    menuargs.update(popup=True)
    self.AddMenu(menuClass, label, menuargs, **kwargs)
  
  def AddPreferences(self, label="Preferences"):
    """
    Add a menu item which opens the preferences dialog.
    """
    self.Append(PrefsItem(label))
  
  def AddSearch(self, menuClass, label="Search", message=None, **kwargs):
    """
    Add a menu item which opens a search dialog.
    """
    message = message if message is not None else label
    self.Append(Function(InputDirectoryItem(MenuHandler, label, message, thumb=R("search.png")), cls=menuClass, **kwargs))
  
  def AddMessage(self, message, title=C['PLUGIN_NAME'], **kwargs):
    """
    Add a menu item which opens a message dialog.
    """
    self.AddMenu(Message, title, message=message, menuargs=kwargs, **kwargs)
  
  def ShowMessage(self, message, title=C['PLUGIN_NAME'], **kwargs):
    """
    Show a message immediately.
    """
    if not kwargs.has_key('header'):
      kwargs['header'] = title
    MediaContainer.__init__(self, message=message, **kwargs)
  

class ABCHighlightsListMenu(ABCMenu):
  """
  Abstract menu for a list of highlights videos
  """
  def getVideoItem(self, id, url=None, title=None, subtitle=None, summary=None, duration=None, thumb=None):
    """
    Get the VideoItem for a highlight video, either by assembling the data we
    already have, or fetching more from mlb.com
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
  

class MainMenu(ABCMenu):
  """
  The top-level menu
  """
  def __init__(self):
    """
    Initialize the menu with menu items.
    """
    # noCache so that changes to the favorite team pref affect the menu
    # immediately
    ABCMenu.__init__(self, noCache=True)
    
    self.AddFavoriteTeamShortcut()
    self.AddMenu(DailyMediaMenu, "Today's Games", date=Util.TimeEastern(), menuNoCache=True)
    self.AddMenu(ArchivedMediaMenu, "Archived Games")
    self.AddMenu(HighlightsMenu, 'Highlights')
    self.AddPreferences()
  
  def AddFavoriteTeamShortcut(self):
    """
    A shortcut to watching your favorite team's video stream
    """
    team = TeamList.favoriteTeam()
    game = None
    stream = None
    
    if team:
      kwargs = {
        "title": C["FAVORITE_MARKER"] + "Watch the " + team.name + " Game",
        "thumb": R('logo-' + team.abbrev + '.png')
      }      
      try:
        game = (game for game in getDailyGames() if game.isFavorite()).next()
        if not game:
          self.AddMessage("It looks like the " + team.name + " aren't playing today.", **kwargs)
        else:
          stream = game.streams.getBest()
          kwargs = {
            "title": C["FAVORITE_MARKER"] + ("Listen to" if stream.kind == "audio" else "Watch") + " the " + team.name + " Game",
            "thumb": R('logo-' + team.abbrev + '.png')
          }
          if stream.pending:
            if game.isFinal():
              self.AddMessage("The game has ended, but the archived stream isn't available yet.", header="Stream Not Available", **kwargs)
            else:
              self.AddMessage("The " + team.name + " stream isn't available yet.", header="Stream Not Available", **kwargs)
          else:
            video_url = C["URL"]["PLAYER"] + "?" + urllib.urlencode({
              'calendar_event_id': game.event_id,
              'content_id': stream.id if stream.id else "",
              'source': 'MLB'
            })
            self.Append(WebVideoItem(video_url, **kwargs))
        return
      except:
        self.AddMessage("Try looking in the \"Today's Games\" menu.", header="Error Loading Stream", **kwargs)
  

class Message(ABCMenu):
  """
  A Menu which displays a message.
  """
  def __init__(self, sender, message=None, **kwargs):
    ABCMenu.__init__(self)
    self.ShowMessage(message, **kwargs)
  

class ArchivedMediaMenu(ABCMenu):
  """
  The Archived Games menu, and its child menus
  """
  def __init__(self, sender, date=None, start=None, end=None, units="y"):
    ABCMenu.__init__(self, title2='Archived Games')
    if units == 'y':
      now = Util.TimeEastern() - datetime.timedelta(days=1)
      end_yesterday = { 'm': now.month, 'd': now.day }
      self.AddMenu(self.__class__, "2010", date={'y': 2010}, start={'m': 3, 'd': 2}, end=end_yesterday, units="m")
      self.AddMenu(self.__class__, "2009", date={'y': 2009}, start={'m': 4, 'd': 5}, end={'m': 11, 'd': 4}, units="m")
    elif units == 'm':
      for i in range(1, 13):
        if start['m'] <= i and i <= end['m']:
          date['m'] = (i, calendar.month_name[i])
          label = "%s %s" % (date['m'][1], date['y'])
          self.AddMenu(self.__class__, label, date=date.copy(), start=start, end=end, units="d")
    elif units == 'd':
      for i in range(1, calendar.monthrange(date['y'], date['m'][0])[1] + 1):
        # TODO simply this mess
        if (date['m'][0] != start['m'] and date['m'][0] != end['m']) or \
           (date['m'][0] == start['m'] and start['m'] != end['m'] and i >= start['d']) or \
           (date['m'][0] != start['m'] and start['m'] != end['m'] and i <= end['d']) or \
           (start['m'] == end['m'] and i >= start['d'] and i <= end['d']):
          label = "%s %s, %s" % (date['m'][1], i, date['y'])
          d = datetime.datetime(year=date['y'], month=date['m'][0], day=i, tzinfo=pytz.timezone("US/Eastern"))
          self.AddMenu(DailyMediaMenu, label, date=d)
  

class DailyMediaMenu(ABCMenu):
  """
  A list of games for a given day.
  """
  def __init__(self, sender, date=Util.TimeEastern(), menuNoCache=False):
    """
    Fetch the list of games for this day from mlb.com, adding each to the menu.
    """
    ABCMenu.__init__(self, title2=sender.itemTitle, viewGroup='Details', noCache=menuNoCache)
    
    games = getDailyGames(date)
    
    # add the games as menu items
    if not games:
      self.ShowMessage("No games found.", sender.itemTitle)
    else:
      for game in games:
        menuopts = {
          'subtitle': game.getSubtitle(),
          'summary': game.getDescription(),
          'thumb': R('icon-video-default.png')
        }
        if game.streams:
          self.AddPopupMenu(GameStreamsMenu, game.getMenuLabel(), menuopts, game=game)
        else:
          messageopts = {
            'title': "No Streams Found",
            'message': "No audio or video streams could be found for this game."
          }
          self.AddMenu(Message, game.getMenuLabel(), menuopts, **messageopts)
  

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
  

class GameStreamsMenu(ABCMenu):
  """
  The game streams popup menu
  """
  def __init__(self, sender, game=None, **kwargs):
    ABCMenu.__init__(self)
    for stream in game.streams:
      if stream.pending:
        self.AddMessage("This stream is not yet available. Try again later.", stream.getMenuLabel(game), header="Not Yet Available")
      elif stream.kind == 'condensed':
        tmp = ABCHighlightsListMenu().getVideoItem(stream.id)
        tmp.title = stream.getMenuLabel(game)
        self.Append(tmp)
      elif stream.pack_id:
        self.AddMenu(HighlightsSearchMenu, stream.getMenuLabel(game), packId=stream.pack_id)
      else:
        video_url = C["URL"]["PLAYER"] + "?" + urllib.urlencode({
          'calendar_event_id': game.event_id,
          'content_id': stream.id if stream.id else "",
          'source': 'MLB'
        })
        self.Append(WebVideoItem(video_url, title=stream.getMenuLabel(game)))
  

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
    self.AddSearch(HighlightsSearchMenu, label='Search Highlights')
  

class HighlightsSearchMenu(ABCHighlightsListMenu):
  """
  A Menu of highlights search results.
  """
  def __init__(self, sender, packId=None, teamId=None, query=None):
    """
    Search mlb.com highlights for either a query, or a team ID, adding each
    result to the menu.
    """
    ABCHighlightsListMenu.__init__(self, viewGroup='Details', title2=sender.itemTitle)
    
    params = C["SEARCH_PARAMS"].copy()
    if packId is not None:
      params.update({"game": packId})
    elif teamId is not None:
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
    
    favoriteteam = TeamList.favoriteTeam()
    if favoriteteam:
      self.AddMenu(submenu, C["FAVORITE_MARKER"] + favoriteteam.fullName(), dict(thumb=R('logo-' + favoriteteam.abbrev + '.png')), teamId=favoriteteam.id)
    
    for team in TeamList.teams:
      if not favoriteteam or favoriteteam != team:
        self.AddMenu(submenu, team.fullName(), dict(thumb=R('logo-' + team.abbrev + '.png')), teamId=team.id)
  


def getDailyGames(date=Util.TimeEastern()):
  now = Util.TimeEastern()
  """
  Get the list of games from mlb.com for a given date, returning yesterday's
  list until 10AM the next morning.
  """
  if now.year == date.year and now.month == date.month and \
     now.day == date.day and date.hour < 10:
    date -= datetime.timedelta(days=1);
  
  return GameList(date)
