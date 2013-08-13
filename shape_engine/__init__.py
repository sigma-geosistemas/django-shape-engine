from django.db.models import CharField, TextField, NullBooleanField, BooleanField, URLField, ImageField, ForeignKey, OneToOneField, EmailField, FileField, SlugField, SmallIntegerField, IntegerField, BigIntegerField, DecimalField, FloatField, DateField, TimeField, DateTimeField, PositiveIntegerField, AutoField
# Defining the possible mapping types
ENGINE_FIONA_MAPPING = {}
ENGINE_NATIVE_MAPPING = {}
ENGINE_CTYPES_MAPPING = {}

try:
    import fiona
    from fiona.crs import from_epsg

    HAS_FIONA = True
    ENGINE_FIONA_MAPPING = { CharField: "str",
                             TextField: "str",
                             NullBooleanField: "str",
                             BooleanField: "str",
                             URLField: "str",
                             ImageField: "str",
                             ForeignKey: "str",
                             OneToOneField: "str",
                             EmailField: "str",
                             FileField: "str",
                             SlugField: "str",
                             AutoField: "int",
                             SmallIntegerField: "int",
                             PositiveIntegerField: "int",
                             IntegerField: "int",
                             BigIntegerField: "int",

                             DecimalField: "float",
                             FloatField: "float",

                             DateField: "str",
                             TimeField: "str",
                             DateTimeField: "str"}

except ImportError:
    HAS_FIONA = False

    try:
        from osgeo import ogr, osr

        HAS_NATIVE_BINDINGS = True
        ENGINE_NATIVE_MAPPING = {CharField: ogr.OFTString,
                                 TextField: ogr.OFTString,
                                 NullBooleanField: ogr.OFTString,
                                 BooleanField: ogr.OFTString,
                                 URLField: ogr.OFTString,
                                 ImageField: ogr.OFTString,
                                 ForeignKey: ogr.OFTString,
                                 OneToOneField: ogr.OFTString,
                                 EmailField: ogr.OFTString,
                                 FileField: ogr.OFTString,
                                 SlugField: ogr.OFTString,

                                 AutoField: ogr.OFTInteger,
                                 SmallIntegerField: ogr.OFTInteger,
                                 PositiveIntegerField: ogr.OFTInteger,
                                 IntegerField: ogr.OFTInteger,
                                 BigIntegerField: ogr.OFTInteger,

                                 DecimalField: ogr.OFTReal,
                                 FloatField: ogr.OFTReal,

                                 DateField: ogr.OFTDate,
                                 TimeField: ogr.OFTTime,
                                 DateTimeField: ogr.OFTDateTime}
    except ImportError:

        HAS_NATIVE_BINDINGS = False
        from django.contrib.gis.gdal.libgdal import lgdal
        from django.contrib.gis.gdal import Driver, OGRGeometry, check_err
        ENGINE_CTYPES_MAPPING = {CharField: ogr.OFTString,
                                 TextField: ogr.OFTString,
                                 NullBooleanField: ogr.OFTString,
                                 BooleanField: ogr.OFTString,
                                 URLField: ogr.OFTString,
                                 ImageField: ogr.OFTString,
                                 ForeignKey: ogr.OFTString,
                                 OneToOneField: ogr.OFTString,
                                 EmailField: ogr.OFTString,
                                 FileField: ogr.OFTString,
                                 SlugField: ogr.OFTString,

                                 AutoField: ogr.OFTInteger,
                                 SmallIntegerField: ogr.OFTInteger,
                                 PositiveIntegerField: ogr.OFTInteger,
                                 IntegerField: ogr.OFTInteger,
                                 BigIntegerField: ogr.OFTInteger,

                                 DecimalField: ogr.OFTReal,
                                 FloatField: ogr.OFTReal,

                                 DateField: ogr.OFTDate,
                                 TimeField: ogr.OFTTime,
                                 DateTimeField: ogr.OFTDateTime}

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

DEFAULT_FIELD_NAME_LENGTH = 10

ENGINE_FIONA = "FIONA"
ENGINE_NATIVE = "NATIVE"
ENGINE_CTYPES = "CTYPES"

ENGINES = [ENGINE_FIONA,
           ENGINE_NATIVE,
           ENGINE_CTYPES]

ENGINE_MAPPINGS = {ENGINE_FIONA: ENGINE_FIONA_MAPPING,
                   ENGINE_NATIVE: ENGINE_NATIVE_MAPPING,
                   ENGINE_CTYPES: ENGINE_CTYPES_MAPPING}