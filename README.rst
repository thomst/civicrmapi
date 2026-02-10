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
Clean and simple bindings to `CiviCRM's API`_. Both `API v3`_ and `API v4`_ are
supported. CiviCRM's API can be accessed either via REST or the command line
tool `cv`_.

.. _CiviCRM's API: https://docs.civicrm.org/dev/en/latest/api/
.. _API v3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
.. _API v4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/
.. _cv: https://github.com/civicrm/cv


Installation
============
::

   pip install civicrmapi


Getting started
===============
There are four ready to use api classes:

- `HttpApiV3`_ - REST API bindings for CiviCRM APIv3
- `HttpApiV4`_ - REST API bindings for CiviCRM APIv4
- `CvApiV3`_ - Using `cv` to access CiviCRM APIv3
- `CvApiV4`_ - Using `cv` to access CiviCRM APIv4

.. _HttpApiV3: https://thomst.github.io/civicrmapi/#civicrmapi.http.HttpApiV3
.. _HttpApiV4: https://thomst.github.io/civicrmapi/#civicrmapi.http.HttpApiV4
.. _CvApiV3: https://thomst.github.io/civicrmapi/#civicrmapi.cv.CvApiV3
.. _CvApiV4: https://thomst.github.io/civicrmapi/#civicrmapi.cv.CvApiV4


All you need to do is to initialize the api of your choice and use it::

    from civicrmapi import CvApiV4

    api = CvApiV4(cv='/path/to/cv', cwd='/path/to/civicrm/root')
    params = {
        "contact_type": "Organization",
        "organization_name": "pretty org",
        }
    result = api.Contact.create(params)



Links
=====
* `Repository <https://github.com/thomst/civicrmapi>`_
* `Documentation <https://thomst.github.io/civicrmapi/>`_
