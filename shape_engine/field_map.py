# coding: utf-8
from collections import Counter
from django.contrib.gis.gdal.field import ROGRFieldTypes
from . import *


class FieldMap(object):

    """
    This class contains data
    for a single field.
    """

    engine = None
    field_in = None
    field_out = None

    def __init__(self, engine, field_in, field_out):

        self.engine = engine
        self.field_in = field_in
        self.field_out = field_out


class FieldMapping(object):

    """
    This class contains all mapping
    data for all layer fields
    """

    engine = None
    field_maps = None

    def __init__(self, field_maps):

        if not field_maps:
            raise AttributeError("field_maps cannot be null.")

        if len(field_maps) <= 0:
            raise AttributeError("field_maps cannot have 0 length.")

        self.engine = field_maps[0].engine
        self.field_maps = field_maps

    def get_field_out_names(self):

        """
        Returns a list with all outgoing field names
        """

        if self.engine == ENGINE_FIONA:
            return self._get_field_out_names_fiona(self.field_maps)

    def get_fiona_schema(self):

        """
        Generates the fiona schema mapping
        """

        if self.engine != ENGINE_FIONA:
            return None

        else:

            dic = {}
            for fm in self.field_maps:
                dic[fm.field_out[0]] = fm.field_out[1]

            return dic

    def get_native_schema(self):

        """
        Generates the native schema mapping
        """

        if self.engine != ENGINE_NATIVE:

            return None

        else:

            return [fm.field_out for fm in self.field_maps]

    def get_ctypes_schema(self):

        """
        Generates the ctypes schema mapping
        """

        if self.engine != ENGINE_CTYPES:
            return None
        else:
            return [fm.field_out for fm in self.field_maps]


    def _get_field_out_names_fiona(self, field_maps):

        """
        Returns a list of field map names for fiona engine
        """

        return [fm.field_out[0] for fm in field_maps]

    def _get_field_out_names_ctypes(self, field_maps):

        """
        Returns a list of field map names for ctypes engine
        """

        return [fm.field_out.name for fm in field_maps]

    def _get_field_out_names_native(self, field_maps):

        """
        Returns a list of field map names for native engine
        """

        return [fm.field_out.GetName() for fm in field_maps]


class BaseFieldMapper(object):

    engine = None

    def __init__(self, engine=None, mapping=None):

        if engine is None:
            raise AttributeError

        if engine not in ENGINES:
            raise AttributeError("Engine is not supported.")

        self.engine = engine

        if mapping is None:
            mapping = ENGINE_MAPPINGS[engine]

        self.mapping = mapping

    def resolve_field_conflicts(self, mappings, size):

        """
        Resolve name conflicts for fields
        """
        new_fields = []
        for i, fm in enumerate(mappings):

            new_name = fm.field_in.name[:size]
            if new_name not in new_fields:
                new_fields.append(new_name)
                continue
            else:
                c = 1
                new_name = "%s_%d" % (new_name[:size -2], c)
                while new_name in new_fields:
                    c += 1
                    new_name = "%s_%d" % (new_name[:size-2], c)

                new_fields.append(new_name)
                if fm.engine == ENGINE_FIONA:
                    fm.field_out = (new_name, fm.field_out[1], )

                if fm.engine == ENGINE_NATIVE:
                    fm.field_out.SetName(new_name)

                if fm.engine == ENGINE_CTYPES:
                    lgdal.OGR_Fld_SetName(fm.field_out, new_name)

    def map_fields(self, fields=[], size=DEFAULT_FIELD_NAME_LENGTH):
        """
        """

        field_maps = []

        for fld in fields:

            fm = self.map_field(fld)
            field_maps.append(fm)

        self.resolve_field_conflicts(field_maps, size=size)

        return FieldMapping(field_maps)

    def map_field(self, field):
        return self._map_field(field)

    def _map_field(self, field):

        raise NotImplemented

class FieldMapper(object):

    """
    Class that creates field mappings correctly
    """

    @staticmethod
    def create(engine, mapping=None):
        if engine == ENGINE_FIONA:
            return FionaFieldMapper(engine, mapping)

        if engine == ENGINE_NATIVE:
            return NativeFieldMapper(engine, mapping)

        if engine == ENGINE_CTYPES:
            return CtypesFieldMapper(engine, mapping)

class FionaFieldMapper(BaseFieldMapper):

    def _map_field(self, field):

        field_type = type(field)
        if field_type not in ENGINE_FIONA_MAPPING:
            raise AttributeError("Mapping not supported with Fiona.")

        fiona_type = ENGINE_FIONA_MAPPING[field_type]
        if fiona_type == "str":
            try:
                max_length = field.max_length or 255
            except:
                max_length = 255

            fiona_type += ":%s" % max_length

        return FieldMap(self.engine, field, (field.name[:DEFAULT_FIELD_NAME_LENGTH], fiona_type))


class NativeFieldMapper(BaseFieldMapper):

    def _map_field(self, field):
        field_type = type(field)
        if field_type not in ENGINE_NATIVE_MAPPING:
            raise AttributeError("Mapping not supported with native bindings.")

        native_type = ENGINE_NATIVE_MAPPING[field_type]
        field_definition = ogr.FieldDefn(field.name[:10], native_type)
        if isinstance(native_type, ogr.OFTString):

            try:
                max_length = field.max_length
            except:
                max_length = 255

            field_definition.SetWidth(max_length)

        return FieldMap(self.engine, field, field_definition)

class CtypesFieldMapper(BaseFieldMapper):

    def _map_field(self, field):
        field_type = type(field)
        if field_type not in ENGINE_CTYPES_MAPPING:
            raise AttributeError("Mapping not supported with ctypes bindings.")

        ctypes = ENGINE_CTYPES_MAPPING[field_type]
        ctypes_int = ROGRFieldTypes[ctypes]
        ctypes_field = lgdal.OGR_Fld_Create(field.name[:10], ctypes_int)

        return FieldMap(self.engine, field, ctypes_field)
