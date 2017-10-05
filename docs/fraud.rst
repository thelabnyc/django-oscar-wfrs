.. fraud:

Fraud Protection
================

To help prevent fraudulent transactions, ``django-oscar-wfrs`` supports pluggable fraud protection modules to screen transactions before they are sent to Wells Fargo. Currently, two modules are included:

===========================================================  ========================================================================================
Package Name                                                 Description
===========================================================  ========================================================================================
wellsfargo.fraud.dummy.DummyFraudProtection                  Default fraud protection class. Doesn't actually screen transactions—just approves
                                                             everything.
wellsfargo.fraud.cybersource.DecisionManagerFraudProtection  Uses Cybersource's Decision Manager via a SOAP API to screen transactions. See
                                                             `Cybersource <https://www.cybersource.com/products/fraud_management/decision_manager/>`_
                                                             for more information.
===========================================================  ========================================================================================


Configuration
-------------

To configure fraud protection, use the ``WFRS_FRAUD_PROTECTION`` setting in Django settings. For example, to configure the Decision Manager module, add the following configuration to your project's settings file.

.. code-block:: python

    WFRS_FRAUD_PROTECTION = {
        'fraud_protection': 'wellsfargo.fraud.cybersource.DecisionManagerFraudProtection',
        'fraud_protection_kwargs': {
            'wsdl': 'https://ics2wstesta.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.141.wsdl',
            'merchant_id': 'my-merchant-id',
            'transaction_security_key': 'my-security-key',
        }
    }

Follow Cybersource's documentation on how to obtain your merchant ID and transaction security key.
