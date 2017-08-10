#!/usr/bin/env python
# -*- coding:utf-8 -*-

import io

from setuptools import setup


version = '0.0.1'


setup(name='python-mijnpon',
      version=version,
      description='Python API for talking to '
                  'Connected cars from PON',
      long_description=io.open('README.rst', encoding='UTF-8').read(),
      keywords='PON Mijn Volkswagen Mijn Skoda Mijn Seat Audi Car Assistant Mijn Volkswagen Bedrijfswagens',
      author='Bram Kragten',
      author_email='mail@bramkragten.nl',
      url='https://github.com/bramkragten/python-mijnpon/',
      packages=['mijnpon'],
      install_requires=['requests>=1.0.0',
                        'requests_oauthlib>=0.7.0']
      )
