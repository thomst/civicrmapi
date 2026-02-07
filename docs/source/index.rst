.. civicrmapi documentation master file, created by
   sphinx-quickstart on Tue Mar 28 10:45:59 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Current version: |version|


Welcome to civicrmapi's documentation!
======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. automodule:: civicrmapi

|


Reference
=========

Base API classes
----------------

.. autoclass:: civicrmapi.base.BaseApi
   :members: VERSION, add_entity, __call__

.. autoclass:: civicrmapi.base.BaseEntity
   :members: NAME, add_action, __call__

.. autoclass:: civicrmapi.base.BaseAction
   :members: NAME, __call__


REST API for v3 and v4
----------------------

.. autoclass:: civicrmapi.rest.RestApiV3
   :members:
   :exclude-members: VERSION

.. autoclass:: civicrmapi.rest.RestApiV4
   :members:
   :exclude-members: VERSION


API v3 and v4 for cv
--------------------

.. autoclass:: civicrmapi.console.ConsoleApiV3
   :members:
   :exclude-members: VERSION

.. autoclass:: civicrmapi.console.ConsoleApiV4
   :members:
   :exclude-members: VERSION


API v3 module
-------------

.. automodule:: civicrmapi.v3
   :members:


API v4 module
-------------

.. automodule:: civicrmapi.v4
   :members:


Exceptions
----------

.. automodule:: civicrmapi.errors
   :members:


|


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
