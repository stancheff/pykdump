#!/usr/bin/env python

# distutils is deprecated in Python 3.10, replace with setuptools

from distutils.core import setup
#from setuptools import setup

setup(name='Pykdump',
      version='0.2',
      description='Python API For Linux Kernel Dumps',
      author='Alex Sidorenko',
      author_email='asid@hp.com',
      url='http://sourceforge.net/projects/pykdump/',
      license='GPL',
      packages=['pykdump'],
     )
