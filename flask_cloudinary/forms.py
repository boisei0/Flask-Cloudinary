# encoding=utf-8
import json
import re

from flask import url_for

from wtforms.widgets import FileInput, HTMLString
from wtforms.fields import FileField
from wtforms import ValidationError

from cloudinary import CloudinaryResource
import cloudinary.utils


class CloudinaryInputWidget(FileInput):
    def __init__(self):
        self._core_options = {
            # 'callback':
        }

    def __call__(self, field, **kwargs):
        options = kwargs.get('options', {})
        kwargs.pop('options')

        params = cloudinary.utils.build_upload_params(**options)
        if 'unsigned' in options:
            params = cloudinary.utils.cleanup_params(params)
        else:
            params = cloudinary.utils.sign_request(params, options)

        if 'resource_type' not in options:
            options['resource_type'] = 'auto'

        html_attrs = {
            'data_url': cloudinary.utils.cloudinary_api_url('upload', **options),
            'data-cloudinary-field': field.name + '-cloudinary',
            'data-form-data': json.dumps(params)
        }

        chunk_size = options.get('chunk_size', None)
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
                u'<input type="hidden" name="{0}" value="{1}">'.format(field.name + '-cloudinary', field.value)
            ]))

        return widget


class CloudinaryJSFileField(FileField):
    widget = CloudinaryInputWidget()  # TODO: Move to __init__

    def __init__(self, options=None, *args, **kwargs):
        if 'validators' in kwargs:
            kwargs['validators'].append(CloudinarySignatureValidator())
        else:
            kwargs['validators'] = CloudinarySignatureValidator()

        if options is None:
            options = {}

        self.widget = CloudinaryInputWidget()


        super(CloudinaryJSFileField, self).__init__()



    def enable_callback(self, request):
        # TODO: Move to __init__ with extra parameter
        pass

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]

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

            self.data = CloudinaryResource(
                public_id,
                format=image_format,
                signature=signature,
                type=upload_type,
                resource_type=resource_type
            )


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
