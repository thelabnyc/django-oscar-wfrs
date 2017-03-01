.. _installation:

Installation
============

Caveats
-------

`django-oscar-wfrs` is built on top of `django-oscar-api` and `django-oscar-api-checkout`. Out of the box, it will not work with the built-in django-oscar (non-ajax) checkout. You can extend

Before Installing
-----------------

In your project, if you haven't already done so, follow the installation instructions for the following dependent libraries.

1. `django-oscar <https://django-oscar.readthedocs.io/en/releases-1.4/internals/getting_started.html#install-oscar-and-its-dependencies>`_
2. `django-oscar-api <https://github.com/django-oscar/django-oscar-api>`_
3. `django-oscar-api-checkout <https://gitlab.com/thelabnyc/django-oscar-api-checkout>`_
4. `django-oscar-bluelight <https://gitlab.com/thelabnyc/django-oscar-bluelight>`_
5. `django-haystack <https://django-haystack.readthedocs.io/en/v2.6.0/tutorial.html#installation>`_

Installing
----------

Install the ``django-oscar-wfrs`` package.

.. code-block:: bash

    $ pip install django-oscar-wfrs

Add ``wellsfargo`` to your ``INSTALLED_APPS``.

.. code-block:: python
    :emphasize-lines: 8

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.postgres',
        'wellsfargo',
    ]

Add the template directory to your template settings.

.. code-block:: python
    :emphasize-lines: 3,9

    from oscar import OSCAR_MAIN_TEMPLATE_DIR
    from oscarbluelight import BLUELIGHT_TEMPLATE_DIR
    from wellsfargo import WFRS_TEMPLATE_DIR

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                WFRS_TEMPLATE_DIR,
                BLUELIGHT_TEMPLATE_DIR,
                OSCAR_MAIN_TEMPLATE_DIR,
            ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'oscar.apps.search.context_processors.search_form',
                    'oscar.apps.promotions.context_processors.promotions',
                    'oscar.apps.checkout.context_processors.checkout',
                    'oscar.apps.customer.notifications.context_processors.notifications',
                    'oscar.core.context_processors.metadata',
                ],
            },
        },
    ]

Add the Wells Fargo views to the OSCAR_DASHBOARD_NAVIGATION setting in ``settings.py``. This will add a new item to the navigation bar in the Oscar dashboard.

.. code-block:: python

    OSCAR_DASHBOARD_NAVIGATION.append({
        'label': 'Wells Fargo',
        'icon': 'icon-globe',
        'children': [
            # Wells Fargo Retail Services Views
            {
                'label': 'Apply for a Credit Line (Wells Fargo)',
                'url_name': 'wfrs-apply-step1',
            },
            {
                'label': 'Add existing Wells Fargo account',
                'url_name': 'wfrs-add-account',
            },
            {
                'label': 'Financing Plans',
                'url_name': 'wfrs-plan-list',
            },
            {
                'label': 'Financing Plan Groups',
                'url_name': 'wfrs-benefit-list',
            },
            {
                'label': 'Credit Applications',
                'url_name': 'wfrs-application-list',
            },
            {
                'label': 'Transfers',
                'url_name': 'wfrs-transfer-list',
            },
        ]
    })

Configure ``django-oscar-api-checkout`` to use ``django-oscar-wfrs`` as a possible payment option. The example below makes Wells Fargo payment available to everyone, but you may wish to set a different permission class and restrict it to staff users, members of a group, etc.

.. code-block:: python

    API_ENABLED_PAYMENT_METHODS = [
        {
            'method': 'wellsfargo.methods.WellsFargo',
            'permission': 'oscarapicheckout.permissions.Public',
        },
    ]

Add ``wellsfargo.models.FinancingPlanBenefit`` to ``BLUELIGHT_BENEFIT_CLASSES`` so that we can use the offers system to control financing plan availability. See :ref:`Concepts <concept_plan_benefits>` for more information on why.

.. code-block:: python

    BLUELIGHT_BENEFIT_CLASSES += [
        ('wellsfargo.models.FinancingPlanBenefit', 'Activate Wells Fargo Plan Number Group'),
    ]

Configure to connect to the Wells Fargo Retail Services SOAP API.

.. code-block:: python

    WFRS_TRANSACTION_WSDL = 'https://retailservices-uat.wellsfargo.com/services/SubmitTransactionService?WSDL'
    WFRS_INQUIRY_WSDL = 'https://retailservices-uat.wellsfargo.com/services/SubmitInquiryService?WSDL'
    WFRS_CREDIT_APP_WSDL = 'https://retailservices-uat.wellsfargo.com/services/SubmitCreditAppService?WSDL'
    WFRS_USER_NAME = 'WS000000000000000'
    WFRS_PASSWORD = 'MY_WELLSFARGO_PASSWORD'
    WFRS_MERCHANT_NUM = '000000000000000'

Configure an encryption key to use when encrypting Wells Fargo Account Numbers. By default this uses symmetric encryption by means of `Fernet <https://cryptography.io/en/latest/fernet/>`_. Alternatively, you may point to a different class implementing the same interface and do encryption by another means, like `KMS <https://aws.amazon.com/kms/>`_ (in which case you wouldn't need to specify a key argument). If you do use Fernet, keep in mind that…

1. …the key should be a a 32-byte sequence that's been base64 encoded.
2. …the key must be a byte sequence, not a string.
3. …the key should not be stored in source code or in the database. Please use an environment variable or a secret store like `Hasicorp Vault <https://www.vaultproject.io/>`_.
4. …you must not lose the key. Losing the key will render any encrypted account number's you have saved unusable.

.. code-block:: python

    import os

    # Key should be something like b'U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8='
    WFRS_SECURITY = {
        'encryptor': 'wellsfargo.security.FernetEncryption',
        'encryptor_kwargs': {
            'key': os.environ.get('WFRS_ENCRYPTION_KEY', '').encode(),
        },
    }

Add the ``django-oscar-wfrs`` views to your projects url configuration.

.. code-block:: python
    :emphasize-lines: 4,5,9,10

    from oscar.app import application as oscar_application
    from oscarapi.app import application as oscar_api
    from oscarapicheckout.app import application as oscar_api_checkout
    from wellsfargo.api.app import application as wfrs_api
    from wellsfargo.dashboard.app import application as wfrs_app

    urlpatterns = [
        # Include plugins
        url(r'^dashboard/wfrs/', include(wfrs_app.urls)),
        url(r'^api/wfrs/', include(wfrs_api.urls)),
        url(r'^api/', include(oscar_api_checkout.urls)),
        url(r'^api/', include(oscar_api.urls)),

        # Include stock Oscar
        url(r'', include(oscar_application.urls)),
    ]
