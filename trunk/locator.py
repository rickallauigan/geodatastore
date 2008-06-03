import wsgiref.handlers
from math import sin, cos, radians, sqrt, atan2

from google.appengine.ext import webapp

from geoserv import Geometry, jsonOutput

class Location(object):
  def __init__(self, geometry):
    self.geometry = geometry
  
  def __repr__(self):
    return '%s: %s' % (self.geometry.name, self.distance)
  
  def __cmp__(self, other):
    return cmp(self.distance, other.distance)
  
  def set_distance(self, lat, lon):
    """
    Calculates the distance between two GPS points (decimal)
    """
    r = 6367442.5 # average earth radius in m
    d_lat = radians(self.geometry.coordinates[0].lat - lat)
    d_lon = radians(self.geometry.coordinates[0].lon - lon)
    x = sin(d_lat/2) ** 2 + \
       cos(radians(self.geometry.coordinates[0].lat)) * cos(radians(lat)) *\
       sin(d_lon/2) ** 2
    y = 2 * atan2(sqrt(x), sqrt(1-x))
    self.distance = r * y


class Request(webapp.RequestHandler):
  def post(self):
    self.locate()

  def get(self):
    self.locate()
    
  def __getParameters(self):
    lat = float(self.request.get('lat'))
    lon = float(self.request.get('lon'))
    if self.request.get('num'):
      num = int(self.request.get('num'))
    else:
      num = 10
    alt = self.request.get('alt')
    callback = self.request.get('callback')
    return lat, lon, num, alt, callback
    
  def locate(self):
    try:
      lat, lon, num, alt, callback = self.__getParameters()
      geometry_query = Geometry.all()
      geometry_query.filter('type = ', 'point')
      
      locations = []
      for geometry in geometry_query:
        location = Location(geometry)
        location.set_distance(lat, lon)
        locations.append(location)
      locations.sort()
      
      geometries = []
      for location in locations[:num]:
        geometries.append(location.geometry)
      
      json, content_type = jsonOutput(geometries, 'search')
      content_type = 'application/json'
      if alt == 'json-in-script':
        out = '%s(%s)' % (callback, json)
        content_type = 'application/javascript'
      else:
        out = json

    except:
      out = "{error:{type:'delete'}}"
      content_type = 'application/json'
        
    self.response.headers['Content-Type'] = content_type
    self.response.out.write(out)

application = webapp.WSGIApplication(
                                     [
                                      ('/locate', Request),
                                       ],
                                     debug=True)

wsgiref.handlers.CGIHandler().run(application)