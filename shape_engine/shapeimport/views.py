from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.views.generic.edit import CreateView, FormView
from django.views.generic.detail import DetailView

from forms import (
    build_shapeimport_form, build_fields_form,
    DONT_IMPORT_KEY
)
from util import ShapefileReader


class ShapeImportCreateView(CreateView):

    fields = ['shapefile']

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class:
            return self.form_class

        return build_shapeimport_form(
            self.model, self.fields
        )


class ShapeImportDetailView(DetailView):

    def get_context_data(self, **kwargs):
        context = super(ShapeImportDetailView, self).get_context_data(**kwargs)
        obj = context['object']
        
        if not obj.finished:
            raise Http404

        context['logs'] = (self.model.log_class.objects
                                               .filter(shape_import=obj)
                                               .order_by('fid'))
        return context


class ShapeImportFieldsView(FormView):

    shape_import = None
    shape_file = None

    def dispatch(self, *args, **kwargs):
        self.shape_import = get_object_or_404(
            self.model, pk=kwargs['pk']
        )

        if self.shape_import.finished:
            raise Http404

        self.shape_file = getattr(
            self.shape_import, self.shape_import.shape_field
        ).file

        return super(ShapeImportFieldsView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        if hasattr(self, 'form_class') and self.form_class:
            return self.form_class

        with ShapefileReader(self.shape_file) as reader:
            form_class = build_fields_form(self.model, reader.fields)

        return form_class

    def form_valid(self, form):
        self.proccess_shape_data(form.data_mapping)
        return redirect(self.shape_import.get_absolute_url())

    def proccess_shape_data(self, mapping):
        with ShapefileReader(self.shape_file) as reader:
            for feature in reader.datasource[0]:
                log = self.shape_import.log_class()
                try:
                    self.proccess_feature(feature, mapping)
                except:
                    log.message = u'An error occurred while saving the feature'
                    log.success = False
                else:
                    log.message = u'Feature imported successfully'
                finally:
                    log.shape_import = self.shape_import
                    log.fid = feature.fid
                    log.save()

        self.shape_import.finished = True
        self.shape_import.save()

    def proccess_feature(self, feature, mapping):
        target_model = self.model.target_model
        pk_name = target_model._meta.pk.name

        obj = None
        if pk_name in mapping:
            obj = target_model.objects.get(pk=feature[mapping[pk_name]])

        if not obj:
            obj = target_model()

        for key in mapping:
            if mapping[key] != DONT_IMPORT_KEY:
                # if mapping[key] == FEATURE_GEOMETRY_KEY:
                #    setattr(obj, key, feature.geom.wkt)
                # else:
                setattr(obj, key, feature[mapping[key]])

        obj.save()
