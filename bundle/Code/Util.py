import time

def parseDuration(duration):
  duration = time.strptime(duration, '%H:%M:%S')
  return str((duration[3]*60*60)+(duration[4]*60)+duration[5])

##############################################################################
def XPathSelectOne(doc, query):
  nodes = doc.xpath(query)
  if len(nodes):
    return str(nodes[0])
  else:
    return ''