# system
import datetime
import pytz
import time

from urlparse import urlparse

# plex
from PMS import Log

##############################################################################
def dump(o):
  Log(str(o))

##############################################################################
def DateURL(date, url):
  return url % (date.year, "%02d" % date.month, "%02d" % date.day)

##############################################################################
def TimeEastern():
  return datetime.datetime.now(pytz.timezone("US/Eastern"))

##############################################################################
def getURLRoot(url):
  parts = urlparse(url)
  return parts.scheme + '://' + parts.netloc

##############################################################################
def parseDuration(duration):
  duration = time.strptime(duration, '%H:%M:%S')
  return str((duration[3]*60*60)+(duration[4]*60)+duration[5])

##############################################################################
def XPathSelectOne(doc, query):
  nodes = doc.xpath(query)
  if len(nodes):
    node = nodes[0]
    try: text = node.text
    except AttributeError:
      text = str(node)
    return text
  else:
    return None
