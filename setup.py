#!/usr/bin/env python3

import os
import setuptools

import bif

_APP_PATH = os.path.dirname(bif.__file__)

with open(os.path.join(_APP_PATH, 'resources', 'README.md')) as f:
      long_description = f.read()

with open(os.path.join(_APP_PATH, 'resources', 'requirements.txt')) as f:
      install_requires = [s.strip() for s in f.readlines()]

with open(os.path.join(_APP_PATH, 'resources', 'version.txt')) as f:
      version = f.read().strip()

setuptools.setup(
    name='bracketed_images_finder',
    version=version,
    description="Find groups of exposure-bracketed images",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='sony bracketing bracketed',
    author='Dustin Oprea',
    author_email='myselfasunder@gmail.com',
    url='https://github.com/dsoprea/bracketed_image_finder',
    license='GPL 2',
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    package_data={
        'bif': [
            'resources/README.md',
            'resources/requirements.txt',
            'resources/version.txt',
        ],
    },
    zip_safe=False,
    install_requires=install_requires,
    scripts=[
        'bif/resources/scripts/bif_find',
    ],
)
