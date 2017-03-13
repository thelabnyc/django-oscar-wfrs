.. _changelog:

Changelog
=========

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
