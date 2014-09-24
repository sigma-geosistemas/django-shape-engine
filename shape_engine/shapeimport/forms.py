# coding: utf-8
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.gis import gdal

from util import ShapefileReader


class ShapefileField(forms.FileField):
    def clean(self, *args, **kwargs):
        shape = super(ShapefileField, self).clean(*args, **kwargs)
        if isinstance(shape, InMemoryUploadedFile):
            with ShapefileReader(shape) as reader:
                try:
                    datasource = reader.datasource
                    layer = datasource[0]

                    for feature in layer:
                        feature.geom

                except gdal.error.OGRException:
                    raise forms.ValidationError(
                        u"Erro ao processar o shape, "
                        u"o arquivo está corrompido."
                    )

        return shape


DONT_IMPORT_KEY = '__si_none'
FEATURE_GEOMETRY_KEY = '__si_geom'


class FieldsForm(forms.Form):
    @property
    def data_mapping(self):
        return {field: self.cleaned_data[field] for field in self.fields}

    @property
    def geom_fields(self):
        return {key: self.data_mapping[key] for key in self.data_mapping
                if self.data_mapping[key] == FEATURE_GEOMETRY_KEY}

    def clean(self, *args, **kwargs):
        non_empty = len([key for key in self.data_mapping
                         if self.data_mapping[key] != DONT_IMPORT_KEY])

        if not non_empty:
            raise ValidationError(u"There aren't any fields to map")

        if not self.geom_fields:
            raise ValidationError(u"You must chose a field to map the geometry"
                                  u"of the feature to")

        return super(FieldsForm, self).clean(*args, **kwargs)


def build_shapeimport_form(import_model, fields):

    """ Creates a generic shape import form for a Model """

    meta = type(
        'Meta',
        (object,),
        {
            'model': import_model,
            'fields': fields
        }
    )

    shapeimport_form = type(
        "{}Form".format(import_model.__name__),
        (forms.ModelForm,),
        {
            'Meta': meta
        }
    )

    return shapeimport_form


def build_fields_form(model, shape_fields):

    """ Creates a generic shape field import form for a Model """

    choices = [
        (DONT_IMPORT_KEY, u"Don't import"),
        (FEATURE_GEOMETRY_KEY, u'Feature Geometry'),
    ]+zip(shape_fields, shape_fields)

    fields = {}
    for field in model.import_fields:
        fields[field] = forms.ChoiceField(
            label=u"Field on the shapefile to be used as the value for '{}'"
                  .format(field),
            choices=choices,
            required=False
        )

    fields_form = type(
        "{}FieldsForm".format(model.target_model.__name__),
        (FieldsForm,),
        fields
    )

    return fields_form
