.. internals:

Internals
=========

Packages
--------

``django-oscar-wfrs`` is split into packages based on area of concerns.

=======================  =============================================================================================
Package Name             Description
=======================  =============================================================================================
wellsfargo               Top level package container. Contains files that django and haystack expect to be in specific
                         spots (models.py, search_indexes.py, etc).
wellsfargo.api           Django Rest Framework based API exposing actions like credit applications and financing plan discover.
wellsfargo.connector     Wrapper for talking to the WFRS SOAP API.
wellsfargo.core          Core components like data structures and exceptions.
wellsfargo.dashboard     Oscar Dashboard application for managing financing plans, searching credit applications, etc.
wellsfargo.security      Encryption utilities for protecting account numbers.
wellsfargo.templatetags  Django Template tags.
wellsfargo.tests         Test suite.
=======================  =============================================================================================
