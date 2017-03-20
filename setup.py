#!/usr/bin/env python
from setuptools import setup, find_packages, Distribution
import codecs
import os.path

# Make sure versiontag exists before going any further
Distribution().fetch_build_eggs('versiontag>=1.2.0')

from versiontag import get_version, cache_git_tag  # NOQA


packages = find_packages('src')

install_requires = [
    'cryptography>=1.6',
    'django-oscar>=1.3.0',
    'django-oscar-api>=1.0.10post1',
    'django-oscar-api-checkout>=0.2.4',
    'django-oscar-bluelight>=0.5.2',
    'django-haystack>=2.5.0',
    'django-localflavor>=1.4.1',
    'djangorestframework>=3.1.0',
    'instrumented-soap>=1.1.0',

    # Legacy. Needed to make migrations run.
    'django-oscar-accounts2>=0.1.0',
]

extras_require = {
    'kms': [
        'boto3>=1.4.4',
    ],
    'development': [
        'elasticsearch>=1.9.0,<2.0.0',
        'flake8>=3.2.1',
        'psycopg2>=2.6.2',
        'PyYAML>=3.12',
        'sphinx>=1.5.2',
        'tox>=2.6.0',
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
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
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
