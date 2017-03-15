.. _concepts:

Concepts
========

Before installation, there are several concepts that are important to understand in regards to how Wells Fargo Retail Services works.


Credit Application
------------------

A credit application is a form filled out by a customer or for a customer when applying for a new account with Wells Fargo. The application data is submitted to Wells Fargo Retail Services and is either Approved or Denied. If approved, the response will include an Account Number.


Account Number
--------------

An account number is a 16 digit long number resembling a credit card number. It uniquely identifies a Wells Fargo account and can be used to authorize or charge payments to the account or to lookup information about the account, such as the credit limit, current balance, payment due, last payment, date, etc.


Transfer
--------

Whenever a transaction is made on an account, this library records metadata about the transaction in the ``TransferMetadata`` model. This metadata includes the user who performed the transaction, the last 4 digits of the customer account number (in plain text), the full customer account number (in an encrypted blob), the plan number, amount, legal disclosure, etc.


Legal Disclosure
----------------

Whenever an authorization or charge is performed on a customs account, Wells Fargo returns a messages that must be displayed to the user who owns the account. The messages generally looks something like this.

    REGULAR TERMS WITH REGULAR PAYMENTS. THE REGULAR RATE IS 27.99%. THIS APR WILL VARY WITH THE MARKET BASED ON THE PRIME RATE.

This messages is stored in a text field on the ``TransferMetadata`` model and should be rendered into the order confirmation template after a user places an order using Wells Fargo Retail Services.


Financing Plan
--------------

A Financing Plan (or just Plan) defines the terms of the financing agreement (APR, term length, etc) that a customer will use to pay for an order. It is defined by a *Plan Number* which is a 4-digit numeric code between *1001* and *9999*. This number if sent to Wells Fargo when performing an authorization or charge. Financing Plan can be added, edited, and deleted in the Oscar dashboard.


.. _concept_plan_benefits:

Financing Plan Benefit
----------------------

Since Financing Plans control what terms a customer gets with they financing, you may wish to have control over which customers have the ability to use which plans. For example, consider the following business rules.

1. Plan 1001 has a 27% APR and should be usable by everyone placing an order on the website.
2. Plan 1002 has a 0% APR, but should only be available for use when an order is over $500.00.

Financing Plan Benefits allow this to happen. A Financing Plan Benefit is a special type of offer / voucher benefit (just like a *$10 off* or *15% off* a normal benefit) whose sole job is to make Financing Plans available to customers. By default, a customer is not considered eligible for any Financing Plans. To model the business rules listed above, we'd do the following in the Oscar dashboard.

1. Create both financing plans, using the *Financing Plans* view at *Dashboard > Wells Fargo > Financing Plans*.
    1. Set the first plans plan number to 1001 and input the correct term length and APR.
    2. Set the second plans plan number to 1002 and input the correct term length and APR.
2. Create two *Financing Plan Groups* using the view at *Dashboard > Wells Fargo > Financing Plan Groups*.
    1. Give the first group a name like *Default Financing* and select plan 1001.
    2. Give the second group a name like *Special Rate Financing* and select plan 1002.
3. Create two offer conditions (*Dashboard > Offers > Conditions*) to match the needed conditions.
    1. The first should be a value condition requiring the basket contain more than $0.01.
    2. The second should be a value condition requiring the basket contain more than $500.00.
4. Tie everything together by creating two offers (*Dashboard > Offers > Offers*).
    1. The first offer should use the $0.01 condition and the *Default Financing* benefit.
    2. The first offer should use the $500.00 condition and the *Special Rate Financing* benefit.

Once this is down, Oscar will make plans available just like it applies other offers and benefits to baskets.
