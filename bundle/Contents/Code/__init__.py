# plex
from PMS import HTTP, Plugin, Prefs
from PMS.Objects import Redirect

# plugin
from Code.Classes import TeamList
from Code.Classes.Menus import MainMenu, MenuHandler
from Code.Config import C

###############################################################################
def Start():
  # default cache time
  HTTP.SetCacheTime(C["CACHE_TTL"])
  
  # Prefetch some content
  # HTTP.PreCache(_GameListURL(), cacheTime=C["GAME_CACHE_TTL"])
  
  Plugin.AddPrefixHandler(C["PLUGIN_PREFIX"], MainMenu, C["PLUGIN_NAME"] + ((" (" + str(C["PLUGIN_VERSION"]) + ")") if C["VERSION_IN_PLUGIN_NAME"] else ""), 'icon-default.png', 'art-default.jpg')
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

###############################################################################
def CreatePrefs():
  Prefs.Add('team', type='enum', default='(None)', label='Favorite Team', values=TeamList.toOptions())
  Prefs.Add('login', type='text', default='', label='MLB.com Login')
  Prefs.Add('password', type='text', default='', label='MLB.com Password', option='hidden')
  Prefs.Add('allowspoilers', type='bool', default=True, label='Show spoilers for in-progress and completed games')

###############################################################################
def UpdateCache():
  HTTP.Request(C["URL"]["TOP_VIDEOS"])

def ValidatePrefs():
  return Redirect(C["PLUGIN_PREFIX"])
