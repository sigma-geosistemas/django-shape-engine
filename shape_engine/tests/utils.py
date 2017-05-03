# coding: utf-8
import unittest
from django.contrib.gis.geos import (
    Point,
    LinearRing,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
)
from shape_engine.utils import GeometryCoercer


class GeometryCoercerTestCase(unittest.TestCase):

    def test_coerce_point_2d(self):

        c = GeometryCoercer()

        point3d = Point(x=0, y=0, z=0, srid=4326)

        self.assertTrue(point3d.hasz)

        point2d = c.coerce(point3d)

        self.assertEquals(point3d.x, point2d.x)
        self.assertEquals(point3d.y, point2d.y)
        self.assertEquals(point3d.srid, point2d.srid)
        self.assertIsNone(point2d.z)

    def test_coerce_point_3d(self):

        c = GeometryCoercer()

        point2d = Point(x=0, y=0, srid=4326)

        self.assertFalse(point2d.hasz)

        point3d = c.coerce(point2d, dimensions=3, z_value=10)

        self.assertEquals(point2d.x, point3d.x)
        self.assertEquals(point2d.y, point3d.y)
        self.assertEquals(point2d.srid, point3d.srid)
        self.assertTrue(point3d.hasz)
        self.assertEquals(10, point3d.z)

    def test_coerce_linestring_2d(self):

        c = GeometryCoercer()
        linestring3d = LineString((0, 0, 2), (1, 1, 2), srid=4326)

        self.assertTrue(linestring3d.hasz)

        linestring2d = c.coerce(linestring3d)

        self.assertFalse(linestring2d.hasz)
        self.assertEquals(linestring2d.srid, linestring3d.srid)

        zip_coords = zip(linestring3d.coords, linestring2d.coords)

        for zc in zip_coords:

            self.assertEquals(zc[0][0], zc[1][0])
            self.assertEquals(zc[0][1], zc[1][1])

    def test_coerce_linestring_3d(self):

        c = GeometryCoercer()

        linestring2d = LineString((0, 0), (1, 1),)
        self.assertFalse(linestring2d.hasz)

        linestring3d = c.coerce(linestring2d, dimensions=3, z_value=10)

        self.assertEquals(linestring2d.srid, linestring3d.srid)
        self.assertTrue(linestring3d.hasz)

        for tupla in linestring3d.coords:

            self.assertEquals(10, tupla[2])

    def test_coerce_linearring_2d(self):

        c = GeometryCoercer()
        linearring3d = LinearRing(((0, 0, 2), (1, 1, 2), (1.5, 1.5, 2), (0, 0, 2)), srid=4326)

        self.assertTrue(linearring3d.hasz)

        linearring2d = c.coerce(linearring3d)

        self.assertFalse(linearring2d.hasz)
        self.assertEquals(linearring2d.srid, linearring3d.srid)

        zip_coords = zip(linearring3d.coords, linearring2d.coords)

        for zc in zip_coords:

            self.assertEquals(zc[0][0], zc[1][0])
            self.assertEquals(zc[0][1], zc[1][1])

    def test_coerce_linearring_3d(self):

        c = GeometryCoercer()

        linearring2d = LinearRing(((0, 0), (1, 1), (1.5, 1.5), (0, 0)), srid=4326)
        self.assertFalse(linearring2d.hasz)

        linearring3d = c.coerce(linearring2d, dimensions=3, z_value=10)

        self.assertEquals(linearring2d.srid, linearring3d.srid)
        self.assertTrue(linearring3d.hasz)

        for tupla in linearring3d.coords:

            self.assertEquals(10, tupla[2])

    def test_coerce_polygon_2d(self):

        c = GeometryCoercer()
        polygon3d = Polygon((((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1))), srid=4326)

        self.assertTrue(polygon3d.hasz)

        polygon2d = c.coerce(polygon3d)

        self.assertFalse(polygon2d.hasz)

        self.assertEquals(polygon3d.area, polygon2d.area)
        self.assertEquals(polygon3d.length, polygon2d.length)
        self.assertEquals(polygon3d.srid, polygon2d.srid)

    def test_coerce_polygon_3d(self):

        c = GeometryCoercer()
        polygon2d = Polygon((((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))), srid=4326)

        self.assertFalse(polygon2d.hasz)

        polygon3d = c.coerce(polygon2d, dimensions=3)

        self.assertTrue(polygon3d.hasz)
        self.assertEquals(polygon3d.area, polygon2d.area)
        self.assertEquals(polygon3d.length, polygon2d.length)
        self.assertEquals(polygon3d.srid, polygon2d.srid)

    def test_coerce_multipoint_2d(self):

        c = GeometryCoercer()
        multipoint3d = MultiPoint((Point(0, 0, 1), Point(1, 1, 1)), srid=4326)
        
        self.assertTrue(multipoint3d.hasz)

        multipoint2d = c.coerce(multipoint3d)

        self.assertFalse(multipoint2d.hasz)
        self.assertEquals(multipoint3d.srid, multipoint2d.srid)

    def test_coerce_multipoint_3d(self):

        c = GeometryCoercer()
        multipoint2d = MultiPoint((Point(0, 0), Point(1, 1)), srid=4326)
        
        self.assertFalse(multipoint2d.hasz)

        multipoint3d = c.coerce(multipoint2d, dimensions=3)

        self.assertTrue(multipoint3d.hasz)
        self.assertEquals(multipoint3d.srid, multipoint2d.srid)

    def test_coerce_multipolygon_2d(self):

        c = GeometryCoercer()
        p1 = Polygon(((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)), srid=4326)
        p2 = Polygon(((2, 2, 1), (2, 3, 1), (3, 3, 1), (3, 2, 1), (2, 2, 1)), srid=4326)
        multipolygon3d = MultiPolygon(p1, p2, srid=4326)

        self.assertTrue(multipolygon3d.hasz)

        multipolygon2d = c.coerce(multipolygon3d)

        self.assertFalse(multipolygon2d.hasz)

    def test_coerce_multipolygon_2d_with_holes(self):

        c = GeometryCoercer()
        exterior = ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1))
        hole1 = ((0.5, 0.5), (0.5, 0.6), (0.6, 0.6), (0.6, 0.5), (0.5, 0.5))
        hole2 = ((0.2, 0.2), (0.2, 0.3), (0.3, 0.3), (0.3, 0.2), (0.2, 0.2))
        p1 = Polygon(exterior , hole1, hole2, srid=4326)
        
        p2 = Polygon(((2, 2, 1), (2, 3, 1), (3, 3, 1), (3, 2, 1), (2, 2, 1)), srid=4326)
        multipolygon3d = MultiPolygon(p1, p2, srid=4326)

        self.assertTrue(multipolygon3d.hasz)

        multipolygon2d = c.coerce(multipolygon3d)

        self.assertFalse(multipolygon2d.hasz)

if __name__ == '__main__':
    unittest.main()
