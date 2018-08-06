#!/usr/bin/env python
from setuptools import setup, find_packages, Distribution
import codecs
import os.path

# Make sure versiontag exists before going any further
Distribution().fetch_build_eggs('versiontag>=1.2.0')

from versiontag import get_version, cache_git_tag  # NOQA


packages = find_packages('src')

install_requires = [
    'cryptography>=2.1.4',
    'django-haystack>=2.6.1',
    'django-localflavor>=2.0',
    'django-oscar-api-checkout>=0.4.0',
    'django-oscar-api>=1.4.0',
    'django-oscar-bluelight>=0.10.0',
    'django-oscar>=1.6.0',
    'djangorestframework>=3.7.0',
    'instrumented-soap>=1.2.0',
]

extras_require = {
    'kms': [
        'boto3>=1.5.7',
    ],
    'development': [
        'coverage>=4.4.2',
        'elasticsearch>=1.9.0,<2.0.0',
        'flake8>=3.5.0',
        'psycopg2cffi>=2.7.7',
        'PyYAML>=3.12',
        'sphinx>=1.6.5',
        'tox>=2.9.1',
        'versiontag>=1.2.0',
    ],
}


def fpath(name):
    return os.path.join(os.path.dirname(__file__), name)


def read(fname):
    return codecs.open(fpath(fname), encoding='utf-8').read()


cache_git_tag()

setup(
    name='django-oscar-wfrs',
    description="An extension on-top of django-oscar-api-checkout to allow interfacing with Wells Fargo Retail Services.",
    version=get_version(pypi=True),
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    author='Craig Weber',
    author_email='crgwbr@gmail.com',
    url='https://gitlab.com/thelabnyc/django-oscar-wfrs',
    license='ISC',
    package_dir={'': 'src'},
    packages=packages,
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
)
