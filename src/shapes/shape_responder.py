# -*- coding: utf-8 -*-
import os
import zipfile
import tempfile
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.contrib.gis.db.models.fields import GeometryField
from . import *
from .engine import ShapefileWriter


class ShpResponder(object):
    def __init__(self, queryset, readme=None, geo_field=None, attribute_fields=None, proj_transform=None,
                 mimetype='application/zip', file_name='shp_download', encoding='latin-1'):

        self.queryset = queryset
        self.readme = readme
        self.geo_field = geo_field
        self.proj_transform = proj_transform
        self.mimetype = mimetype
        self.file_name = smart_str(file_name)
        self.attribute_fields = attribute_fields or []
        self.model_field_names = self.queryset.model._meta.get_all_field_names()
        self.encoding = encoding

    def __call__(self, *args, **kwargs):
        tmp = self.write_shapefile_to_tmp_file(self.queryset)
        return self.zip_response(tmp, self.file_name, self.mimetype, self.readme)

    def get_attributes(self):
        # TODO: control field order as param
        attr = self.attribute_fields
        if not self.attribute_fields:
            fields = self.queryset.model._meta.fields
            attr = [f.name for f in fields if not isinstance(f, GeometryField)]
        return attr

    def get_geo_field(self):

        if isinstance(self.geo_field, GeometryField):
            return self.geo_field

        fields = self.queryset.model._meta.fields
        geo_fields = [f for f in fields if isinstance(f, GeometryField)]
        geo_fields_names = ', '.join([f.name for f in geo_fields])

        if len(geo_fields) > 1:
            if not self.geo_field:
                raise ValueError(
                    "More than one geodjango geometry field found, please specify which to use by name using the 'geo_field' keyword. Available fields are: '%s'" % geo_fields_names)
            else:
                geo_field_by_name = [fld for fld in geo_fields if fld.name == self.geo_field]
                if not geo_field_by_name:
                    raise ValueError(
                        "Geodjango geometry field not found with the name '%s', fields available are: '%s'" % (
                        self.geo_field, geo_fields_names))
                else:
                    geo_field = geo_field_by_name[0]
        elif geo_fields:
            geo_field = geo_fields[0]
        else:
            raise ValueError('No geodjango geometry fields found in this model queryset')

        return geo_field

    def write_shapefile_to_tmp_file(self, queryset):
        tmp = tempfile.NamedTemporaryFile(suffix='.shp', mode='w+b')
        # we must close the file for GDAL to be able to open and write to it
        tmp.close()
        args = tmp.name, queryset, self.get_geo_field()

        if HAS_FIONA:
            self.write_with_fiona(*args)
        else:
            if HAS_NATIVE_BINDINGS:
                self.write_with_native(*args)
            else:
                self.write_with_native(*args)

        return tmp.name

    def write_zip_file(self, zipfile_path, readme=None):
        shapefile_path = self.write_shapefile_to_tmp_file(self.queryset)
        zip = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
        files = ['shp', 'shx', 'prj', 'dbf']
        for item in files:
            filename = '%s.%s' % (shapefile_path.replace('.shp', ''), item)
            zip.write(filename, arcname='%s.%s' % (os.path.basename(zipfile_path).replace('.zip', ''), item))
        if readme:
            zip.writestr('README.txt', readme)
        zip.close()

    def zip_response(self, shapefile_path, file_name, mimetype, readme=None):
        buffer = StringIO()
        zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)
        files = ['shp', 'shx', 'prj', 'dbf']
        for item in files:
            filename = '%s.%s' % (shapefile_path.replace('.shp', ''), item)
            zip.write(filename, arcname='%s.%s' % (file_name.replace('.shp', ''), item))
        if readme:
            zip.writestr('README.txt', readme)
        zip.close()
        buffer.flush()
        zip_stream = buffer.getvalue()
        buffer.close()

        # Stick it all in a django HttpResponse
        response = HttpResponse()
        response['Content-Disposition'] = 'attachment; filename=%s.zip' % file_name.replace('.shp', '')
        response['Content-length'] = str(len(zip_stream))
        response['Content-Type'] = mimetype
        response.write(zip_stream)
        return response

    def write_with_fiona(self, tmp_name, queryset, geofield):

        shp_writer = ShapefileWriter.create(engine=ENGINE_FIONA)
        shp_writer.write_records(queryset, self.get_attributes(), geofield, tmp_name, self.proj_transform)

    def write_with_native(self, tmp_name, queryset, geofield):

        shp_writer = ShapefileWriter.create(engine=ENGINE_NATIVE)
        shp_writer.write_records(queryset, self.get_attributes(), geofield, tmp_name, self.proj_transform)

    def write_with_ctypes(self, tmp_name, queryset, geofield):

        shp_writer = ShapefileWriter.create(engine=ENGINE_CTYPES)
        shp_writer.write_records(queryset, self.get_attributes(), geofield, tmp_name, self.proj_transform)