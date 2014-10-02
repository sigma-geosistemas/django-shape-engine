# coding: utf-8
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.gis import gdal
from django.utils.translation import ugettext_lazy as _

from util import ShapefileReader
from exceptions import HandlerNotFound, HandlerError, CompressedShapeError


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
                        _(u"Error while processing the shapefile, "
                          u"the file is corrupted.")
                )

                except (HandlerError, 
                        HandlerNotFound,
                        CompressedShapeError) as e:
                    raise forms.ValidationError(e.message)

        return shape


DONT_IMPORT_KEY = '__SI_NONE'


class FieldsForm(forms.Form):
    @property
    def data_mapping(self):
        return {field: self.cleaned_data[field] for field in self.fields}

    def clean(self, *args, **kwargs):
        non_empty = len([key for key in self.data_mapping
                         if self.data_mapping[key] != DONT_IMPORT_KEY])

        if not non_empty:
            raise ValidationError(_(u"There aren't any fields to map."))

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
        (DONT_IMPORT_KEY, _(u"Don't import"))
    ]+zip(shape_fields, shape_fields)

    fields = {}
    for field in model.import_fields:
        fields[field] = forms.ChoiceField(
            label=_(u"Field on the shapefile to be used as the value for '{}'")
                  .format(field),
            choices=choices,
            required=False
        )

    fields_form = type(
        "{}FieldsForm".format(model.__name__),
        (FieldsForm,),
        fields
    )

    return fields_form
