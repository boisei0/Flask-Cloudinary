# encoding=utf-8
from copy import deepcopy
import json
import re

from flask import url_for, current_app

from wtforms.widgets import FileInput, HTMLString
from wtforms.fields import FileField
from wtforms import ValidationError

from cloudinary import CloudinaryResource
import cloudinary.utils
import cloudinary.uploader


# noinspection PyClassHasNoInit
class CloudinaryMixin:
    def to_resource(self, value):
        if not value:
            return None

        m = re.search(r'^([^/]+)/([^/]+)/v(\d+)/([^#]+)#([^/]+)$', value)
        if not m:
            raise ValueError(u'Invalid format')

        resource_type = m.group(1)
        upload_type = m.group(2)
        version = m.group(3)
        filename = m.group(4)
        signature = m.group(5)

        m = re.search(r'(.*)\.(.*)', filename)
        if not m:
            raise ValueError(u'Invalid file name')

        public_id = m.group(1)
        image_format = m.group(2)

        return CloudinaryResource(
            public_id,
            format=image_format,
            signature=signature,
            type=upload_type,
            resource_type=resource_type
        )


def cl_init_js_callbacks(form):
    for field in form:
        if isinstance(field, CloudinaryJSFileField):
            field.enable_callback()


class CloudinaryInputWidget(FileInput):
    def __init__(self, **options):
        self.core_options = dict()
        self.core_options.update(options)

    def __call__(self, field, **kwargs):
        if 'options' in kwargs:
            options = kwargs.pop('options')
        else:
            options = {}

        options_ = deepcopy(self.core_options)
        options_.update(options)

        params = cloudinary.utils.build_upload_params(**options_)
        if 'unsigned' in options_:
            params = cloudinary.utils.cleanup_params(params)
        else:
            params = cloudinary.utils.sign_request(params, options_)

        if 'resource_type' not in options_:
            options['resource_type'] = 'auto'

        html_attrs = {
            'data_url': cloudinary.utils.cloudinary_api_url('upload', **options_),
            'data-cloudinary-field': field.name + '-cloudinary',
            'data-form-data': json.dumps(params)
        }

        chunk_size = options_.get('chunk_size', None)
        if chunk_size:
            html_attrs['data-max-chunk-size'] = chunk_size

        if 'class_' in kwargs:
            kwargs['class_'] += u' cloudinary-fileupload'
        elif 'class' in kwargs:
            kwargs['class'] += u' cloudinary-fileupload'
        else:
            html_attrs['class_'] = 'cloudinary-fileupload'

        kwargs.update(html_attrs)

        widget = super(CloudinaryInputWidget, self).__call__(field, **kwargs)

        if 'value' in kwargs:
            if isinstance(kwargs['value'], CloudinaryResource):
                value_string = kwargs['value'].get_presigned()
            else:
                value_string = kwargs['value']

            widget = HTMLString(u''.join([
                widget,
                u'<input type="hidden" name="{0}" value="{1}">'.format(field.name + '-cloudinary', value_string)
            ]))

        return widget


class CloudinaryJSFileField(FileField, CloudinaryMixin):
    def __init__(self, options=None, *args, **kwargs):
        if 'validators' in kwargs:
            kwargs['validators'].append(CloudinarySignatureValidator())
        else:
            kwargs['validators'] = [CloudinarySignatureValidator()]

        if options is None:
            options = {}

        self.widget = CloudinaryInputWidget(**options)

        super(CloudinaryJSFileField, self).__init__(*args, **kwargs)

    def enable_callback(self):
        self.widget.core_options['callback'] = url_for('flask_cloudinary.static', filename='html/cloudinary_cors.html',
                                                       _external=True)

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]


class CloudinaryUnsignedJSFileField(CloudinaryJSFileField):
    def __init__(self, upload_preset, options=None, *args, **kwargs):
        if options is None:
            options = {}
        options = options.copy()
        options.update({"unsigned": True, "upload_preset": upload_preset})

        super(CloudinaryUnsignedJSFileField, self).__init__(options, *args, **kwargs)


class CloudinaryFileField(FileField):
    def __init__(self, options=None, autosave=True, *args, **kwargs):
        self.autosave = autosave
        self.options = options or {}
        super(CloudinaryFileField, self).__init__(*args, **kwargs)

    # noinspection PyAttributeOutsideInit
    def process_formdata(self, valuelist):
        super(CloudinaryFileField, self).process_formdata(valuelist)

        if not self.data:
            pass
        if self.autosave:
            self.data = cloudinary.uploader.upload_image(self.data, **self.options)


# Validators:
class CloudinarySignatureValidator(object):
    """Validate the signature"""

    def __init__(self, message=None):
        if not message:
            message = u'Signature mismatch'

        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return
        if not field.data.validate():
            raise ValidationError(self.message)
