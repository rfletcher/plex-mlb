##############################################################################
def XPathSelectOne(doc, query):
  nodes = doc.xpath(query)
  if len(nodes):
    return str(nodes[0])
  else:
    return ''