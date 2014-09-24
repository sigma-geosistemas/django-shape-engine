# coding: utf-8
import zipfile
import tempfile
import os
import time
import shutil
import abc
import mimetypes

from django.contrib.gis import gdal
from django.utils.translation import ugettext as _

from exceptions import ZipShapeError


class ShapefileHandler(object):
    ''' Interface for handlers of different compressed shapefiles '''

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def MIME_TYPES(self):
        raise NotImplementedError

    @abc.abstractproperty
    def namelist(self):
        raise NotImplementedError

    @abc.abstractmethod
    def extract(self, dir):
        raise NotImplementedError


class HandlerFactory(object):
    _handlers = set()

    @classmethod
    def register_handler(cls, handler_class):
        if not issubclass(handler_class, ShapefileHandler):
            raise Exception("n implementa a interface rs")
        cls._handlers.add(handler_class)
        return handler_class

    @classmethod
    def get(cls, file):
        if hasattr(file, 'content_type'):
            content_type = file.content_type
        else:
            content_type = mimetypes.guess_type(file.name)[0]

        for handler in cls._handlers:
            if content_type in handler.MIME_TYPES:
                return handler(file)

        raise Exception("Não achou ninguém que abre")
shapefile_handler = HandlerFactory.register_handler


@shapefile_handler
class ZipShapefileHandler(ShapefileHandler):

    MIME_TYPES = (
        'application/zip',
        'application/x-zip',
        'application/x-zip-compressed',
        'application/octet-stream',
        'application/x-compress',
        'application/x-compressed',
        'multipart/x-zip',
    )

    def __init__(self, file):
        self._file = zipfile.ZipFile(file)

    @property
    def namelist(self):
        return self._file.namelist()

    def extract(self, dir):
        self._file.extractall(dir)


class ShapefileReader(object):

    REQUIRED_EXTENSIONS = ['.dbf', '.prj', '.shp', '.shx']

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        shutil.rmtree(self._tmp_dir)

    def __init__(self, file):
        self.file = file

        self._tmp_dir = os.path.join(tempfile.gettempdir(),
                                     "{:.9f}".format(time.time()))

        self._datasource = None

        os.makedirs(self._tmp_dir)

    @property
    def datasource(self):
        if not self._datasource:
            self._datasource = self._get_datasource()
        return self._datasource

    @property
    def fields(self):
        return self.datasource[0].fields

    def _get_datasource(self):

        handler = HandlerFactory.get(self.file)

        ext_set = set(ShapefileReader.REQUIRED_EXTENSIONS)
        files_name = None
        for name in handler.namelist:
            fname, ext = os.path.splitext(name)

            if not files_name:
                files_name = fname
            elif fname != files_name:
                raise ZipShapeError(_(u'The files are not all from the same  '
                                      u'shapefile.'))

            if ext == '.shp':
                shapefile_name = name

            ext_set.discard(ext)

        if ext_set:
            raise ZipShapeError(_(u'The following files are missing in the '
                                  u'shapefile: {}').format(list(ext_set)))

        handler.extract(self._tmp_dir)
        shapefile_path = os.path.join(self._tmp_dir, shapefile_name)

        return gdal.DataSource(shapefile_path)
