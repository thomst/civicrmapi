"""
----------
civicrmapi
----------
This package provides a convenient way to access `CiviCRM`_'s API from Python
applications. It supports both `API`_ verions `v3`_ and `v4`_ as REST API and
via the console command `cv`_.

.. _CiviCRM: https://docs.civicrm.org/
.. _API: https://docs.civicrm.org/dev/en/latest/api/
.. _v3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
.. _v4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/
.. _cv: https://github.com/civicrm/cv


Getting Started
---------------
There are four ready to use api classes:

- :class:`~civicrmapi.rest.RestApiV3` - REST API bindings for CiviCRM APIv3
- :class:`~civicrmapi.rest.RestApiV4` - REST API bindings for CiviCRM APIv4
- :class:`~civicrmapi.console.ConsoleApiV3` - Using `cv` to access CiviCRM APIv3
- :class:`~civicrmapi.console.ConsoleApiV4` - Using `cv` to access CiviCRM APIv4

All you need to do is to initialize the api of your choice and use it::

    from civicrmapi import ConsoleApiV4

    api = ConsoleApiV4(cv='/path/to/cv', cwd='/path/to/civicrm/root')
    params = {
        "contact_type": "Organization",
        "organization_name": "pretty org",
        }
    result = api.Contact.create(params)


Concepts
--------
There are three main base classes an api binding is built of:

- :class:`~base.BaseApi` - Base class for all API implementations
- :class:`~base.BaseEntity` - Base class for CiviCRM entities
- :class:`~base.BaseAction` - Base class for CiviCRM actions

Initializing an api class will automatically equip it with entities, which
themselves are equipped with actions - each as instance attributes. And on each
level of this hierarchy an api call can be performed. The api, its entities and
their actions are all callable.

The following ways of performing an api call are equivalent::

    from civicrmapi import RestApiV4

    api = RestApiV4(url='https://example.org/civicrm', api_key='your_api_key')
    params = {'sequential': 1}

    # Calling the action instance.
    result = api.Contact.get(params)

    # Calling the entity instance passing the action as parameter.
    result = api.Contact('get', params)

    # Calling the api instance  passing the entity and action as parameters.
    result = api('Contact', 'get', params)


The standard entities and actions for each api version are defined within the
the corresponding modules :mod:`~.v3` and :mod:`~.v4`. You can also implement
special behavior like custom validation, result parsing or error handling by
writing your own api, entity or action subclasses.
"""

from .base import BaseAction
from .base import BaseEntity
from .base import BaseApi
from .errors import InvalidApiCall
from .errors import InvalidResponse
from .rest import RestApiV3
from .rest import RestApiV4
from .console import ConsoleApiV3
from .console import ConsoleApiV4