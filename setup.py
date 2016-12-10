# encoding=utf-8
from setuptools import setup

with open('requirements.txt', 'r') as f:
    required = f.read().splitlines()


setup(
    name='Flask-Cloudinary',
    version='0.1',
    license='MIT',
    author='Arlena Derksen',
    author_email='arlena@hubsec.eu',
    description='Library that ports the Django stuff of Cloudinary to Flask/Jinja2/WTForms',
    packages=['flask_cloudinary'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=required
)
