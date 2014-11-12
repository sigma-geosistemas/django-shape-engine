# coding: utf-8
from django.contrib.gis.geos import *

class GeometryCoercer(object):

	"""Class responsbible to coerce
	a determinate geometry to 2d or
	3d. If you are coercing to 3d, 
	zero will be assumed, unless you
	specify the z_value"""

	def __init__(self):
		pass

	def coerce(self, geometry, dimensions=2, z_value=0):

		"""Coerces a geometry to the specified number of
		dimensions. Values available are 2d or 3d"""

		if dimensions < 2:
			raise ValueError("Its not possible to coerce a geometry to less than two dimensions.")

		if dimensions > 3:
			raise ValueError("Its not possible to coerce a geometry to higher than three dimensions.")

		# geometry already is 3d
		if geometry.hasz and dimensions == 3:
			return geometry

		if geometry.geom_type == "Point":
			return self._coerce_point(geometry, dimensions, z_value)

		if geometry.geom_type == "LineString":
			return self._coerce_linestring(geometry, dimensions, z_value)

		if geometry.geom_type == "LinearRing":
			return self._coerce_linearring(geometry, dimensions, z_value)

		if geometry.geom_type == "Polygon":
			return self._coerce_polygon(geometry, dimensions, z_value)

		if geometry.geom_type == "MultiPoint":
			return self._coerce_multipoint(geometry, dimensions, z_value)

		if geometry.geom_type == "MultiLineString":
			return self._coerce_multilinestring(geometry, dimensions, z_value)

		if geometry.geom_type == "MultiPolygon":
			return self._coerce_multipolygon(geometry, dimensions, z_value)

		if geometry.geom_type == "GeometryCollection":
			return self._coerce_geometrycollection(geometry, dimensions, z_value)

		raise ValueError("The geometry type is not supported for coercion.")

	def _coerce_point(self, geometry, dimensions=2, z_value=0):
		
		if not geometry.hasz and dimensions == 3:
			return Point(x=geometry.x, y=geometry.y, z=z_value, srid=geometry.srid)

		if geometry.hasz and dimensions == 2:
			return Point(x=geometry.x, y=geometry.y, srid=geometry.srid)

	def _coerce_linestring(self, geometry, dimensions=2, z_value=0):
		
		coords = geometry.coords

		if not geometry.hasz and dimensions == 3:
			
			new_coords = tuple([(c[0], c[1], z_value) for c in coords])
			return LineString(new_coords, srid=geometry.srid)

		if geometry.hasz and dimensions == 2:
			
			new_coords = tuple([(c[0], c[1]) for c in coords])
			return LineString(new_coords, srid=geometry.srid)

	def _coerce_linearring(self, geometry, dimensions=2, z_value=0):
		
		return self._coerce_linestring(geometry, dimensions, z_value)

	def _coerce_polygon(self, geometry, dimensions=2, z_value=0):

		coords = geometry.coords

		if not geometry.hasz and dimensions == 3:

			new_rings = [self._coerce_linearring(LinearRing(ring, srid=geometry.srid), dimensions=3, z_value=z_value) for ring in coords]	

		if geometry.hasz and dimensions == 2:

			new_rings = [self._coerce_linearring(LinearRing(ring, srid=geometry.srid)) for ring in coords]
			
		return Polygon(*new_rings, srid=geometry.srid)

	def _coerce_multipoint(self, geometry, dimensions=2, z_value=0):
		
		new_points = []
		for p in geometry:
			new_points.append(self._coerce_point(p, dimensions, z_value))

		return MultiPoint(new_points, srid=geometry.srid)

	def _coerce_multilinestring(self, geometry, dimensions=2, z_value=0):
		
		new_linestrings = []

		for l in geometry:
			new_linestrings.append(self._coerce_linestring(l, dimensions, z_value))

		return MultiLineString(new_linestrings, srid=geometry.srid)

	def _coerce_multipolygon(self, geometry, dimensions=2, z_value=0):
		
		new_polygons = []

		for p in geometry:
			new_polygons.append(self._coerce_polygon(p, dimensions, z_value))

		return MultiPolygon(new_polygons, srid=geometry.srid)

	def _coerce_geometrycollection(self, geometry, dimensions=2, z_value=0):
		raise ValueError("Not implemented")