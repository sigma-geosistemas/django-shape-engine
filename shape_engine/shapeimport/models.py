import os

from django.db import models
from django.db.models.fields import Field
from django.utils.translation import ugettext_lazy as _lz
from django.core.urlresolvers import reverse

import forms


class ShapefileField(models.FileField):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.ShapefileField,
            'max_length': self.max_length
        }
        if 'initial' in kwargs:
            defaults['required'] = False
            defaults.update(kwargs)

        return Field.formfield(self, **defaults)


class ShapeImportMixIn(models.Model):

    class Meta:
        abstract = True

    shapefile = ShapefileField(
        upload_to='media/shapeimport',
        help_text=_lz(u'Compressed shapefile, must contain '
                      u'the .shp, .shx, .dbf and .prj files')
    )
    shape_field = 'shapefile'

    finished = models.BooleanField(
        default=False,
        verbose_name=_lz(u'Finished?'),
        help_text=_lz(u"Indicates wether or not the import of the shapefile."
                      u"is finished (False means there's something pending, "
                      u"such as choosing the fields to map to).")
    )

    @property
    def file_name(self):
        return os.path.basename(self.shapefile.name)

    def get_absolute_url(self):
        if self.finished:
            return reverse(self.detail_url, kwargs={'pk': self.pk})
        else:
            return reverse(self.fields_url, kwargs={'pk': self.pk})

    @property
    def import_model(self):
        raise NotImplementedError

    @property
    def import_fields(self):
        raise NotImplementedError

    @property
    def logs_attr(self):
        raise NotImplementedError


class ShapeImportLogMixIn(models.Model):

    class Meta:
        abstract = True

    @property
    def shape_import(self):
        raise NotImplementedError

    fid = models.IntegerField(_lz(u'FID of the feature in the shapefile.'))
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255)
