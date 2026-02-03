=====================
Welcome to civicrmapi
=====================

.. image:: https://img.shields.io/badge/python-3.8+-blue
   :target: https://img.shields.io/badge/python-3.8+-blue
   :alt: python: 3.8+

.. image:: https://github.com/thomst/civicrmapi/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/thomst/civicrmapi/actions/workflows/tests.yml
   :alt: Tests

.. image:: https://coveralls.io/repos/github/thomst/civicrmapi/badge.svg?branch=main
   :target: https://coveralls.io/github/thomst/civicrmapi?branch=main
   :alt: Coveralls


Description
===========
Clean and simple bindings to CiviCRM's API. Both APIv3 and APIv4 are supported.
CiviCRM's API can be accessed either via REST or the command line tool `cv`.


Installation
============
::

   pip install civicrmapi


Getting started
===============
There are four ready to use api classes:

- `RestApiV3` - REST API bindings for CiviCRM APIv3
- `RestApiV4` - REST API bindings for CiviCRM APIv4
- `ConsoleApiV3` - Using `cv` to access CiviCRM APIv3
- `ConsoleApiV4` - Using `cv` to access CiviCRM APIv4

All you need to do is to initialize the api of your choice and use it::

    from civicrmapi import ConsoleApiV4

    api = ConsoleApiV4(cv='/path/to/cv', cwd='/path/to/civicrm/root')
    params = {
        "contact_type": "Organization",
        "organization_name": "pretty org",
        }
    result = api.Contact.create(params)



Links
=====
* `Repository <https://github.com/thomst/civicrmapi>`_
* `Documentation <https://thomst.github.io/civicrmapi/>`_
