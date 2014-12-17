import os

from django.db import models
from django.db.models.fields import Field
from django.utils.translation import ugettext_lazy as _

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
        ordering = ['-created_at']

    shapefile = ShapefileField(
        upload_to='shapeimport',
        help_text=_(u'Compressed shapefile, must contain '
                    u'the .shp, .shx, .dbf and .prj files')
    )
    shape_field = 'shapefile'

    finished = models.BooleanField(
        default=False,
        verbose_name=_(u'Finished?'),
        help_text=_(u"Indicates wether or not the import of the shapefile."
                    u"is finished (False means there's something pending, "
                    u"such as choosing the fields to map to).")
    )

    created_at = models.DateTimeField(
        verbose_name=_(u'Created at'),
        auto_now_add=True
    )

    @property
    def file_name(self):
        return os.path.basename(self.shapefile.name)

    def get_absolute_url(self):
        return self.finished and self.get_detail_url() or self.get_fields_url()

    def get_fields_url(self):
        raise NotImplementedError

    def get_detail_url(self):
        raise NotImplementedError

    @property
    def import_model(self):
        raise NotImplementedError

    @property
    def import_fields(self):
        raise NotImplementedError

    @property
    def import_geometry(self):
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

    fid = models.IntegerField(_(u'FID of the feature in the shapefile.'))
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255)
