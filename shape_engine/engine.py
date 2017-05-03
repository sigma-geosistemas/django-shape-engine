# coding: utf-8
import json
from django.contrib.gis.gdal import OGRGeomType, SpatialReference, CoordTransform
from . import *
from .field_map import FieldMapper


class ShapefileWriter(object):

    @staticmethod
    def create(engine):

        if engine == ENGINE_FIONA:
            return FionaShapefileWriter(engine)

        if engine == ENGINE_CTYPES:
            return CtypesShapefileWriter(engine)

        if engine == ENGINE_NATIVE:
            return NativeShapefileWriter(engine)


class BaseShapefileWriter(object):

    model_field_names = []
    driver_name = None
    choice_display = False

    def __init__(self, engine=ENGINE_FIONA, driver_name="ESRI Shapefile"):
        if engine not in ENGINES:
            raise AttributeError("Engine not supported")

        self.engine = engine
        self.driver_name = driver_name

    def _reset_writer_state(self):
        self.model_field_names = []
        self.id_counter = 1

    # override
    def _get_geometry_type(self, geofield):
        raise NotImplemented

    # override
    def _get_output_srs(self, in_srid, out_srid):
        raise NotImplemented

    # override
    def _create_layer(self, tmp_name, fieldmapping, geofield, output_srid, encodign="utf-8", layer_name=""):
        raise NotImplemented

    def _get_fields_from_atributes(self, queryset, attributes):

        """
        Returns a list of fields
        """

        fields = queryset.model._meta.fields
        return [f for f in fields if f.name in attributes]

    # override
    def write_records(self,
                      queryset,
                      attributes,
                      geofield,
                      tmp_name="output_shapefile",
                      out_srid=None,
                      choice_display=True,
                      encoding="utf-8"):

        if hasattr(geofield, "srid"):
            in_srid = SpatialReference(geofield.srid)
        else:
            in_srid = SpatialReference(geofield._srid)

        self._reset_writer_state()

        self.model_field_names = [f.name for f in queryset.model._meta.get_fields()]
        self.choice_display = choice_display

        features = []

        export_fields = self._get_fields_from_atributes(queryset, attributes)

        field_mapper = FieldMapper.create(self.engine)
        fieldmapping = field_mapper.map_fields(export_fields)
        layer, datasource = self._create_layer(tmp_name, fieldmapping, geofield, out_srid, encoding)

        self._write_records(queryset, fieldmapping, geofield, layer, in_srid, out_srid)

        self._flush(layer, datasource)
        self._close(layer, datasource)

    # override
    def _write_records(self, queryset, fieldmapping, geofield, layer, in_srid, out_srid):

        raise NotImplemented

    # override
    def _flush(self, layer, datasource=None):

        raise NotImplemented

    # override
    def _close(self, layer, datasource=None):

        raise NotImplemented

    def _get_item_id(self, item):

        pk = getattr(item, "pk")

        if not isinstance(pk, int):
            pk = self.id_counter
            self.id_counter += 1

        return pk

    # override
    def _get_geometry_value(self, item, geofield, in_srid, out_srid):
        raise NotImplemented

    def _get_field_value(self, item, field_mapping):

        """
        Encapsulates the correct way to
        extract a field value
        """

        field_in = field_mapping.field_in
        field_name = field_in.name

        if field_mapping.field_in.name in self.model_field_names:

            internal_type = field_in.get_internal_type()

            if field_in.choices:
                return self._get_choice_value(item, field_name)

            if internal_type == "ForeignKey":
                return unicode(getattr(item, field_name))

            if internal_type in ('DateTimeField', 'TimeField'):
                return getattr(item, field_mapping.field_in.name).isoformat()

            return getattr(item, field_mapping.field_in.name)

        else:

            # callable

            value = self._get_prop_value(item, field_name)

        if value is None:
            value = ""

        return value

    def _get_prop_value(self, item, field_name):

        if callable(getattr(item, field_name)):
            return getattr(item, field_name)()

        return None

    def _get_choice_value(self, item, field_name):

        """
        Correctly returns a choice field value, using
        the choice_display parameter
        """

        if self.choice_display:

            return getattr(item, "get_%s_display" % field_name)

        else:

            return getattr(item, field_name)

    def _create_features(self, queryset, fieldmapping, geofield, layer, in_srid, out_srid):

        features = []

        for item in queryset:
            features.append(self._create_feature(item, fieldmapping, geofield, layer, in_srid, out_srid))

        return features

    # override
    def _create_feature(self, item, fieldmapping, geofield, layer, in_srid, out_srid):
        raise NotImplemented


class FionaShapefileWriter(BaseShapefileWriter):

    def _get_geometry_type(self, geofield):
        if hasattr(geofield, 'geom_type'):
            geometry_type = OGRGeomType(geofield.geom_type).name
        else:
            geometry_type = OGRGeomType(geofield._geom).name

        return geometry_type

    def _get_output_srs(self, in_srid, out_srid):
        if out_srid:
            out_srs = SpatialReference(out_srid)
        else:
            out_srs = SpatialReference(in_srid)

        return from_epsg(out_srs.srid)

    def _create_layer(self, tmp_name, fieldmapping, geofield, output_srid, encoding="utf-8", layer_name=""):
        if hasattr(geofield, 'srid'):
            in_srs = SpatialReference(geofield.srid)
        else:
            in_srs = SpatialReference(geofield._srid)

        if output_srid:
            out_srs = SpatialReference(output_srid)
        else:
            out_srs = in_srs

        crs = from_epsg(out_srs.srid)

        properties = fieldmapping.get_fiona_schema()
        schema = {"geometry" : self._get_geometry_type(geofield),
                  "properties": properties}

        shapefile = fiona.open(tmp_name,
                               "w",
                               driver=self.driver_name,
                               crs=crs,
                               schema=schema,
                               encoding=encoding)
        return shapefile

    def _flush(self, layer):
        layer.flush()

    def _close(self, layer):
        layer.close()

    def _get_geometry_value(self, item, geofield, in_srid, out_srid):

        geometry = getattr(item, geofield.name)

        if geometry:

            ogr_geom = geometry.ogr

            if out_srid and out_srid != in_srid:

                if type(out_srid) is int:
                    out_srid = SpatialReference(out_srid)

                if type(in_srid) is int:
                    in_srid = SpatialReference(in_srid)

                ct = CoordTransform(in_srid, out_srid)
                ogr_geom.transform(ct)

            return ogr_geom.geojson

        else:
            # skip
            return None

    def _create_feature(self, item, fieldmapping, geofield, layer, in_srid, out_srid):
        geojson = self._get_geometry_value(item, geofield, in_srid, out_srid)

        if geojson is None:
            return

        properties = {}

        for fm in fieldmapping.field_maps:

            value = self._get_field_value(item, fm)

            properties[fm.field_out[0]] = value

        geometry = json.loads(geojson)
        record = {"geometry": geometry,
                  "id": self._get_item_id(item),
                  "properties": properties}
        return record

    def write_records(self,
                      queryset,
                      attributes,
                      geofield,
                      tmp_name="output_shapefile",
                      out_srid=None,
                      choice_display=True,
                      encoding="utf-8"):

        if hasattr(geofield, "srid"):
            in_srid = SpatialReference(geofield.srid)
        else:
            in_srid = SpatialReference(geofield._srid)

        self._reset_writer_state()

        self.model_field_names = [f.name for f in queryset.model._meta.get_fields()]
        self.choice_display = choice_display

        export_fields = self._get_fields_from_atributes(queryset, attributes)
        field_mapper = FieldMapper.create(engine=ENGINE_FIONA, mapping=None)
        fieldmapping = field_mapper.map_fields(export_fields)

        if hasattr(geofield, 'srid'):
            in_srs = SpatialReference(geofield.srid)
        else:
            in_srs = SpatialReference(geofield._srid)

        if out_srid:
            out_srs = SpatialReference(out_srid)
        else:
            out_srs = in_srs

        crs = from_epsg(out_srs.srid)

        properties = fieldmapping.get_fiona_schema()
        schema = {"geometry" : self._get_geometry_type(geofield),
                  "properties": properties}
        datasource = None

        with fiona.open(tmp_name,
                        "w",
                        driver=self.driver_name,
                        crs=crs,
                        schema=schema,
                        encoding=encoding) as layer:

            self._write_records(queryset, fieldmapping, geofield, layer, in_srid, out_srid)

    def _write_records(self, queryset, fieldmapping, geofield, layer, in_srid, out_srid):

        features = self._create_features(queryset, fieldmapping, geofield, layer, in_srid, out_srid)

        for feature in features:

            layer.write(feature)

class NativeShapefileWriter(BaseShapefileWriter):

    def _get_geometry_type(self, geofield):
        if hasattr(geofield, 'geom_type'):
            ogr_type = OGRGeomType(geofield.geom_type).num
        else:
            ogr_type = OGRGeomType(geofield._geom).num

        return ogr_type

    def _get_geometry_value(self, item, geofield, in_srid, out_srid):

        geometry = getattr(item, geofield.name)

        if geometry:
            ogr_geom = ogr.CreateGeometryFromWkt(geometry.wkt)
            if out_srid and out_srid != in_srid:
                ct = osr.CoordinateTransformation(in_srid, out_srid)
                ogr_geom.Transform(ct)

            return ogr_geom
        else:
            return None

    def _get_output_srs(self, in_srid, out_srid):
        pass

    def _create_layer(self, tmp_name, fieldmapping, geofield, output_srid, encodign="utf-8", layer_name=""):

        driver = ogr.GetDriverByName(self.driver_name)
        datasource = driver.CreateDataSource(tmp_name)
        if datasource is None:
            raise Exception("Could not create shapefile.")

        srs = osr.SpatialReference()
        srs = srs.ImportFromEPSG(output_srid)
        geometry_type = self._get_geometry_type(geofield)

        layer = datasource.CreateLayer("lyr", srs=srs, geom_type=geometry_type)
        return layer, datasource

    def write_records(self,
                      queryset,
                      attributes,
                      geofield,
                      tmp_name="output_shapefile",
                      out_srid=None,
                      choice_display=True,
                      encoding="utf-8"):
        pass

    def _write_records(self, queryset, fieldmapping, geofield, layer, in_srid, out_srid):

        features = self._create_features(queryset, fieldmapping, geofield, layer, in_srid, out_srid)

        for feature in features:

            check_err(layer.CreateFeature(feature))

    def _flush(self, layer, datasource=None):
        if layer is None:
            raise AttributeError("layer cannot be null while saving data.")

        if datasource is None:
            raise AttributeError("datasource cannot be null while saving data.")

        datasource.Destroy()

    def _close(self, layer, datasource=None):
        pass

    def _create_feature(self, item, fieldmapping, geofield, layer, in_srid, out_srid):

        ogr_geom = self._get_geometry_value(item, geofield, in_srid, out_srid)

        if ogr_geom is None:
            return

        feature_definition = layer.GetLayerDefn()
        feature = ogr.Feature(feature_definition)

        for fm in fieldmapping.field_maps:

            value = self._get_field_value(item, fm)
            feature.SetField(fm.field_out.GetName(), value)

        check_err(feature.SetGeometry(ogr_geom))

        return feature

class CtypesShapefileWriter(BaseShapefileWriter):

    def _get_geometry_type(self, geofield):
        if hasattr(geofield, 'geom_type'):
            ogr_type = OGRGeomType(geofield.geom_type).num
        else:
            ogr_type = OGRGeomType(geofield._geom).num

        return ogr_type


    def _get_geometry_value(self, item, geofield, in_srid, out_srid):
        geometry = getattr(item, geofield.name)

        if geometry:
            ogr_geom = OGRGeometry(geometry.wkt, out_srid)
            if out_srid and out_srid != in_srid:
                ct = CoordTransform(in_srid, out_srid)
                ogr_geom.transform(ct)

            return ogr_geom
        else:
            return None

    def _get_output_srs(self, in_srid, out_srid):
        pass

    def _create_layer(self, tmp_name, fieldmapping, geofield, output_srid, encodign="utf-8", layer_name=""):
        driver = ogr.GetDriverByName(self.driver_name)
        datasource = lgdal.OGR_Dr_CreateDataSource(driver._ptr, tmp_name, None)
        if datasource is None:
            raise Exception("Could not create shapefile.")

        if hasattr(geofield, 'srid'):
            native_srs = SpatialReference(geofield.srid)
        else:
            native_srs = SpatialReference(geofield._srid)

        if output_srid:
            output_srs = SpatialReference(output_srid)
        else:
            output_srs = native_srs

        geometry_type = self._get_geometry_type(geofield)
        layer = lgdal.OGR_DS_CreateLayer(datasource,
                                         "lyr",
                                         output_srs,
                                         geometry_type,
                                         None)
        return layer, datasource

    def _write_records(self, queryset, fieldmapping, geofield, layer, in_srid, out_srid):

        features = self._create_features(queryset, fieldmapping, geofield, layer, in_srid, out_srid)

        for feature in features:
            check_err(lgdal.OGR_L_SetFeature(layer, feature))


    def _flush(self, layer, datasource=None):
        if layer is None:
            raise AttributeError("layer cannot be null while saving data.")

        if datasource is None:
            raise AttributeError("datasource cannot be null while saving data.")

        check_err(lgdal.OGR_L_SyncToDisk(layer))
        lgdal.OGR_DS_Destroy(datasource)
        lgdal.OGRCleanupAll()

    def _close(self, layer, datasource=None):
        pass

    def _create_feature(self, item, fieldmapping, geofield, layer, in_srid, out_srid):

        ogr_geom = self._get_geometry_value(item, geofield, in_srid, out_srid)

        if ogr_geom is None:
            return

        feature_definition = lgdal.OGR_L_GetLayerDefn(layer)
        feature = lgdal.OGR_F_Create(feature_definition)

        for i, fm in enumerate(fieldmapping.field_maps):

            value = self._get_field_value(item, fm)
            lgdal.OGR_F_SetField(feature, i, value)

        check_err(lgdal.OGR_F_SetGeometry(feature, ogr_geom._ptr))

        return feature
