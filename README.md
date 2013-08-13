django-shape-engine
===================

Django shape-engine is a simple implementation that will allow 
you to export django querysets to shapefiles.

The shape-engine currently supports three different backends:

* Fiona (recommended);
* Native;
* CTypes;

The only one tested is the Fiona backend.

This code is all based on Dane Springmeyer (@springmeyer) 
django-shapes and Luiz Fernando Vital (@luizvital) Fiona
implementation.

The original code (https://bitbucket.org/springmeyer/django-shapes/wiki/Home) exported everything to a single data-type: strings. 
This code can look into the field type and guess what data type it
needs to have in the shapefile.

The only caveat is that the support for properties the original project
had is missing.

This is very very alpha stage, but the Fiona implementation works.

If there are bugs (I'm pretty sure some will appear :)), please let me know.

## Export dictionary

If you need to support custom fields, you can alter the dictionaries that will be
used to map the field types.

Basically, the field map for Fiona is:

```python
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

```
