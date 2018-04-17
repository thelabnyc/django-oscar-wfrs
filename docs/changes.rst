.. _changelog:

Changelog
=========

0.12.1
------------------
- Update compatible django-oscar-api-checkout version

0.12.0
------------------
- Add new API endpoint for estimating loan payments based on advertised plan thresholds.

0.11.0
------------------
- Add support for Wells Fargo's Pre-Qualification (soft-credit check) API.

0.10.1
------------------
- Fix corrupted package build in version ``0.10.0``.

0.10.0
------------------
- Add support for django-localflavor 2.0 by switching to using django-phonenumber-field for phone number fields.
    - This introduces a breaking change in the application APIs. Phone number fields were previously expected to be submitted in the format: ``5555555555``. They must now be submitted in a format accepted by `python-phonenumbers <https://github.com/daviddrysdale/python-phonenumbers>`_, such as ``+1 (555) 555-5555`` or ``+1 555.555.5555``.
- Remove previously squashed migrations.
- Remove dependency on django-oscar-accounts and django-oscar-accounts2.
- Fix Django 2.0 deprecation warnings.

0.9.1
------------------
- Patch package requirements to require django-localflavor less than 2.0.

0.9.0
------------------
- Add automatic retries to transactions when they encounter a network issue.

0.8.0
------------------
- Add ability to gate transaction using pluggable fraud screen modules. By default fraud screening is disabled.

0.7.2
------------------
- Add support for Django 1.11 and Oscar 1.5
- Add new field to the FinancingPlan model to contain a price threshold value.
    - While the offers system is still used to determine what plans a basket is eligible for, sometimes plan data is needed before a product is in the basket. For example, you may wish to advertise a monthly payment price for a product outside of the basket context. Previously the ``is_default_plan`` flag was used for this purpose. Now, each plan can have a price threshold set in the ``product_price_threshold``. Then, those threshold values can be used to determine which plan to display for each product. For example, if you configure plan 0001 with a threshold of $100.00 and plan 0002 with a threshold of $200.00, a product costing $150.00 would display a monthly price calculated based on plan 0001 while a product costing $500.00 would display a monthly price calculated based on plan 0002. The ``is_default_plan`` flag still exists and can be used as a fallback to products not meeting any of the configured thresholds.
    - Add template override in the sandbox store to demonstrate this behavior.

0.7.1
------------------
- Add new field to the FinancingPlan model to contain a superscript number, corresponding to fine print displayed elsewhere on the page.

0.7.0
------------------
- Fix 404ing JS in Oscar Dashboard
- Add several new columns to the Credit Application dashboard:
    - Merchant Name used for application
    - Application Source
    - Requested Credit Amount
    - Resulting Credit Limit
    - Order total of first related order
    - Merchant name used for order
- Fixes exception thrown when trying to decrypt invalid data using KMS backend
- Add button to export a CSV of credit applications from the dashboard
- Make Wells Fargo Benefits use offer conditions to consume basket lines
    - Use oscar-bluelight's offer groups feature to allow stacking other discounts with financing benefits. The recommended set-up is to place all Wells Fargo related offers into an offer group of their own, configured with a lower priority than any other group.

0.6.7
------------------
- Add new multi-encryptor class that combines multiple other encryptors together. This allows key rotation and graceful migration between different encryption methods.

0.6.6
------------------
- Handle pending application responses separately from denied responses. They now throw different API exceptions with different error messages and error codes.
- Add some basic dashboard view tests.

0.6.5
------------------
- Add foreign key from TransferMetadata to APICredentials used to make the transfer.

0.6.4
------------------
- Fix bug which prevented adding new plan groups via the dashboard.
- Adds unit tests for financing plan and financing plan group dashboard forms.

0.6.3
------------------
- Save last 4 digits of resulting account number to credit application models.
- Add ``TransferMetadata.purge_encrypted_account_number`` method.
- Handle ValidationError when submitting a transaction to prevent 500 errors in checkout.
- Fix 500 error in Credit App API when SOAP API returned a validation issue.
- Fix install documentation regarding API credentials.

0.6.2
------------------
- Fix bug when migrating account numbers to new encrypted fields.

0.6.1
------------------
- Moved Fernet encryption class from ``wellsfargo.security.FernetEncryption`` to ``wellsfargo.security.fernet.FernetEncryption``.
- Added alternative `AWS KMS <https://aws.amazon.com/kms/>`_ encryption class as ``wellsfargo.security.kms.KMSEncryption``.

0.6.0
------------------
- **Major Release. Breaking Changes.**
- Drop dependency on django-oscar-accounts.
- Stop tracking accounts in database.
- Account numbers are now encrypted at rest.

0.5.0
------------------
- Add support for Django 1.10, Python 3.6.
- Drop support for Django 1.8, Python 3.4.

0.4.3
------------------
- During reconciliation with WFRS, adjust credit limit before doing compensating transaction.

0.4.2
------------------
- Make application date times display in localized timezone in the dashboard search-results table.

0.4.1
------------------
- Upgrade dependencies.

0.4.0
------------------
- Add improved credit application search functionality to dashboard.
- Fix bug where AccountInquiryResult.reconcile() would sometimes attempt to make a debit with a negative amount.

0.3.1
------------------
- Add boolean for controlling whether or not to display a credit application form to the client.

0.3.0
------------------
- Move API credentials into database, optionally triggered by user group.

0.2.6
------------------
- Add a relation between wellsfargo.AccountMetadata and order.BillingAddress.

0.2.5
------------------
- Prevent creating invalid WFRS Plan Group Benefits in the standard bluelight benefit dashboard.

0.1.0
------------------
- Initial release.
