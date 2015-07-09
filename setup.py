# -*- coding: utf-8 -*-

import re
from codecs import open

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


requires = [
    "beautifulsoup4==4.4.0",
    "requests==2.7.0"
]

packages = ['nsicrawler']


version = ''

with open('nsicrawler/__init__.py', 'r', encoding='utf-8') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')


setup(
    name='nsicrawler',
    version=version,
    description='Simple crawler for product catalogue',
    author='Tomasz Łaszczuk',
    author_email='tomaszlaszczuk@gmail.com',
    include_package_data=True,
    install_requires=requires,
    packages=packages,
    package_dir={'nsicrawler': 'nsicrawler'},
    zip_safe=False,
    classifiers=(
        'Development Status :: Development',
        'Intended Audience :: Developers',
        'Natural Language :: English/Polish',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ),
)
