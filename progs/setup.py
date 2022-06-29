#!/usr/bin/env python

# distutils is deprecated in Python 3.10, replace with setuptools

from distutils.core import setup
#from setuptools import setup

setup(name='LinuxDump',
      version='0.2',
      description='Linux Dump Analysis Using Pykdump',
      author='Alex Sidorenko',
      author_email='asid@hp.com',
      url='http://sourceforge.net/projects/pykdump/',
      license='GPL',
      #package_dir = {'': '..'},
      packages=['LinuxDump', 'LinuxDump.inet', 'LinuxDump.fs'],
     )
