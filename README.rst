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
Clean and simple bindings to `CiviCRM`_'s `API`_. Both `APIv3`_ and `APIv4`_ are
supported. CiviCRM's API can be accessed either via REST or the command line
tool `cv`_.

.. _CiviCRM: https://docs.civicrm.org/
.. _API: https://docs.civicrm.org/dev/en/latest/api/
.. _APIv3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
.. _APIv4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/
.. _cv: https://github.com/civicrm/cv


Installation
============
::

   pip install civicrmapi


Getting started
===============
There are four ready to use api classes:

- `RestApiV3`_ - REST API bindings for CiviCRM APIv3
- `RestApiV4`_ - REST API bindings for CiviCRM APIv4
- `ConsoleApiV3`_ - Using `cv` to access CiviCRM APIv3
- `ConsoleApiV4`_ - Using `cv` to access CiviCRM APIv4

.. _RestApiV3: https://thomst.github.io/civicrmapi/#civicrmapi.rest.RestApiV3
.. _RestApiV4: https://thomst.github.io/civicrmapi/#civicrmapi.rest.RestApiV4
.. _ConsoleApiV3: https://thomst.github.io/civicrmapi/#civicrmapi.console.ConsoleApiV3
.. _ConsoleApiV4: https://thomst.github.io/civicrmapi/#civicrmapi.console.ConsoleApiV4


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
