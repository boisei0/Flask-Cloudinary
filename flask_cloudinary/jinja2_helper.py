# encoding=utf-8
import json
import os

from flask import url_for

from jinja2.ext import Extension
from jinja2 import nodes, Template

import cloudinary

from flask_cloudinary import LIBRARY_ROOT


class CloudinaryIncludesExtension(Extension):
    tags = {'cloudinary_includes'}

    def __init__(self, environment):
        super(CloudinaryIncludesExtension, self).__init__(environment)

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        processing = nodes.Const(None)

        if parser.stream.current.test('name') and parser.stream.look().test('assign'):
            name = next(parser.stream).value
            parser.stream.skip()
            value = parser.parse_expression()

            if name == 'processing':
                processing = value

        call = self.call_method('_render_includes', [processing], lineno=lineno)
        output = nodes.CallBlock(call, [], [], [])
        output.set_lineno(lineno)

        return output

    def _render_includes(self, processing, caller=None):
        with open(os.path.join(LIBRARY_ROOT, 'templates', 'cloudinary_includes.html'), 'r') as template_file:
            template = Template(template_file.read())

        if not processing:
            processing = False

        return template.render(url_for=url_for, processing=processing)


class CloudinaryJSConfigExtension(Extension):
    CLOUDINARY_JS_CONFIG_PARAMS = ("api_key", "cloud_name", "private_cdn", "secure_distribution", "cdn_subdomain")

    tags = {'cloudinary_js_config'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        call = self.call_method('_render_config', lineno=lineno)
        output = nodes.CallBlock(call, [], [], [])
        output.set_lineno(lineno)

        return output

    def _render_config(self, caller=None):
        config = cloudinary.config()
        params = dict(
            params=json.dumps(dict(
                (param, getattr(config, param)) for param in self.CLOUDINARY_JS_CONFIG_PARAMS
                if getattr(config, param, None)
            ))
        )

        with open(os.path.join(LIBRARY_ROOT, 'templates', 'cloudinary_js_config.html'), 'r') as template_file:
            template = Template(template_file.read())

        return template.render(params=params)


class CloudinaryTagExtension(Extension):
    tags = {'cloudinary'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        options = dict()

        # Parse the arguments
        source = parser.parse_expression()

        if parser.stream.skip_if('comma'):
            first = True
            while parser.stream.current.type != 'block_end':
                if not first:
                    parser.stream.expect('comma')
                first = False

                # Lookahead to see if this is an assignment (an option)
                if parser.stream.current.test('name') and parser.stream.look().test('assign'):
                    name = next(parser.stream).value
                    parser.stream.skip()
                    value = parser.parse_expression()

                    options[nodes.Const(name)] = value

        node_options = []
        for k, v in options.iteritems():  # TODO: Do this the Python3 friendly way
            node_options.append(nodes.Pair(k, v))

        node_options = nodes.Dict(node_options)

        call = self.call_method('_render', [source, node_options], lineno=lineno)
        output = nodes.CallBlock(call, [], [], [])
        output.set_lineno(lineno)

        return output

    def _render(self, source, options, caller=None):
        if not isinstance(source, cloudinary.CloudinaryResource):
            source = cloudinary.CloudinaryResource(source)

        return source.build_url(**options)