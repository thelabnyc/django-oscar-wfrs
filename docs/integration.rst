.. _integration:

Integration
===========

Since ``django-oscar-api-checkout`` and ``django-oscar-wfrs`` are designed around the idea of client-side AJAX centric checkouts, theres a bit of custom work to do to integrate ``django-oscar-wfrs`` into your client side application. Here is a basic overview of what the client-side application needs to do. The URLs below assume you followed the :ref:`installation instruction <installation>` and installed the WFRS API at ``/api/wfrs/``.

Submitting a Credit Application
-------------------------------

Make a ``POST`` request to ``/api/wfrs/apply/`` specifying the region and the application type. This will return a link to the Application endpoint to continue with.

=========  ==========================================
Parameter  Values
=========  ==========================================
region     ``US`` (United States) or ``CA`` (Canada)
app_type   ``I`` (Individual) or ``J`` (Joint)
=========  ==========================================

::

    POST /api/wfrs/apply/

    region=US&app_type=I

The API will return the URL of the appropriate form.

::

    {
        "url": https://mysite.com/api/wfrs/apply/us-individual/
    }

Make an ``OPTIONS`` request to the returned URL to get information about which fields need to make up the application form.

::

    OPTIONS /api/wfrs/apply/us-individual/

The API will return the fields and validation rules applicable to the selected form.

::

    {
        "actions": {
            "POST": {
                "region": {
                    "type": "choice",
                    "required": false,
                    "read_only": false,
                    "label": "Region",
                    "choices": [
                        {
                            "display_name": "United States",
                            "value": "US"
                        }
                    ]
                },
                "app_type": {
                    "type": "choice",
                    "required": false,
                    "read_only": false,
                    "label": "App type",
                    "choices": [
                        {
                            "display_name": "Individual",
                            "value": "I"
                        }
                    ]
                },
                "language": {
                    "type": "choice",
                    "required": false,
                    "read_only": false,
                    "label": "Language",
                    "choices": [
                        {
                            "display_name": "English",
                            "value": "E"
                        }
                    ]
                },
                "purchase_price": {
                    "type": "integer",
                    "required": false,
                    "read_only": false,
                    "label": "Requested Credit Amount",
                    "min_value": 0,
                    "max_value": 99999
                },
                "main_first_name": {
                    "type": "string",
                    "required": true,
                    "read_only": false,
                    "label": "First Name",
                    "max_length": 15
                },
            }
        }
    }

Using that response, build and display the application form to the customer to fill out. However this is down will vary greatly depending on the architecture of your client-side code.

After the user has completely filled out the form, ``POST`` the data back to the same URL as JSON.

::

    POST /api/wfrs/apply/us-individual/

    {
        "region": "US",
        "app_type": "I",
        "language": "E",
        "purchase_price": "1000",
        "main_first_name": "Rusty"
    }

If any of the data is invalid or if the credit application is denied by Wells Fargo, a response like this (with a description of the error) will be returned.

::

    {
        "main_last_name": [
            "This field may not be blank."
        ]
    }

If the application was successfully approved by Wells Fargo, a response like this will be returned.

::

    {
        "account_number": "9999999999999999",
        "credit_limit": "7500.00",
        "balance": "0.00",
        "open_to_buy": "7500.00",
    }

You should then display the account number to the user and tell them to write it down, print it, etc. If lost, they will not be able to easily recover it, as the application has not recorded or saved it anywhere.


Placing an Order
----------------

Once a customer has indicated that they would like to pay using WFRS, make a ``GET`` request to ``/api/wfrs/plans/`` to list which plans the user is eligible to use. This is based on the offers data configured in the :ref:`Oscar dashboard <concept_plan_benefits>`.

::

    GET /api/wfrs/plans/

The API will return the plans available to the user.

::

    [
        {
            "id": 1,
            "plan_number": 1001,
            "description": "Regular Terms Apply",
            "apr": "28.99",
            "term_months": 0,
            "allow_credit_application": false
        },
        {
            "id": 2,
            "plan_number": 1002,
            "description": "Special rate of 0% APR with for 48 months",
            "apr": "0.00",
            "term_months": 48,
            "allow_credit_application": true
        }
    ]

Use this data to construct a form to allow the customer to enter their account number and to pick which financing plan they would like to use.

After they've entered both their account number and picked their financing plan, they can place their order. To place the order, submit the checkout data to the ``django-oscar-api-checkout`` API endpoint with WFRS data included in the payment block.

==============  ==============================================
Parameter       Values
==============  ==============================================
account_number  The customer's full 16 digit account number
                devoid of spaces or other characters.
financing_plan  The ID (primary key) of the selected financing
                plan. *Note: not the plan number.*
==============  ==============================================

::

    POST /api/checkout/

    {
        "payment": {
            "wells-fargo": {
                "enabled": true,
                "account_number": "9999999999999999",
                "financing_plan": 2
            }
        },
        "guest_email": "joe@example.com",
        "basket": "/api/baskets/1/",
        "shipping_address": {
            "first_name": "Joe",
            "last_name": "Schmoe",
            "line1": "234 5th Ave",
            "line4": "Manhattan",
            "postcode": "10001",
            "state": "NY",
            "country": "/api/countries/US/",
            "phone_number": "+1 (717) 467-1111",
        },
        "billing_address": {
            "first_name": "Joe",
            "last_name": "Schmoe",
            "line1": "234 5th Ave",
            "line4": "Manhattan",
            "postcode": "10001",
            "state": "NY",
            "country": "/api/countries/US/",
            "phone_number": "+1 (717) 467-1111",
        }
    }

Upon submission, ``django-oscar-wfrs`` attempts to authorize payment on the given account. Regardless of whether or not payment is successful, the order is object is created and is returned in the response.

::

    {
        "number": "1234",
        ...
    }

You application must then check the status of the payment source to see if it was completed successfully.

::

    GET /api/checkout/payment-states/

If the authorization was successful, the response will look like this.

::

    {
        "order_status": "Authorized",
        "payment_method_states": {
            "wells-fargo": {
                "status": "Complete",
                "amount": "200.00",
                "required_action": null
            }
        }
    }

If the authorization was unsuccessful, the response will look like this.

::

    {
        "order_status": "Payment Declined",
        "payment_method_states": {
            "wells-fargo": {
                "status": "Declined",
                "amount": "200.00",
                "required_action": null
            }
        }
    }

If you receive a successfully authorized response, you can now forward the customer to the order thank you page. Otherwise, you should inform them that the payment authorization was unsuccessful and that they should re-enter their account number and try again. Once they do this, you can retry the ``POST`` to ``/api/checkout/``. If the authorization continues to fail, this most likely means that either they do not have a valid account number or that there isn't enough credit left on their account to cover the purchase.
