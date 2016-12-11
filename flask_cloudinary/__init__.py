# encoding=utf-8
import os

from flask import Blueprint

LIBRARY_ROOT = os.path.abspath(os.path.dirname(__file__))


class FlaskCloudinary(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('CLOUDINARY_URL_PREFIX', '/cloudinary-helpers')

        blueprint = Blueprint('flask_cloudinary', __name__, static_folder='static', template_folder='templates',
                              url_prefix=app.config['CLOUDINARY_URL_PREFIX'])

        # TODO: Do we need any urls specified?

        app.register_blueprint(blueprint)

        app.jinja_env.add_extension('flask_cloudinary.jinja2_helper.CloudinaryTagExtension')
        app.jinja_env.add_extension('flask_cloudinary.jinja2_helper.CloudinaryURLExtension')
        app.jinja_env.add_extension('flask_cloudinary.jinja2_helper.CloudinaryIncludesExtension')
        app.jinja_env.add_extension('flask_cloudinary.jinja2_helper.CloudinaryJSConfigExtension')
