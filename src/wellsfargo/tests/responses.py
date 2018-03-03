import os.path
_base = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(_base, 'responses/transaction_successful.xml'), 'r') as f:
    transaction_successful = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/transaction_denied.xml'), 'r') as f:
    transaction_denied = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/inquiry_successful.xml'), 'r') as f:
    inquiry_successful = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/inquiry_failed.xml'), 'r') as f:
    inquiry_failed = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/otb_denied.xml'), 'r') as f:
    otb_denied = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/otb_error.xml'), 'r') as f:
    otb_error = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/otb_successful.xml'), 'r') as f:
    otb_successful = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/prequal_successful.xml'), 'r') as f:
    prequal_successful = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/prequal_failed.xml'), 'r') as f:
    prequal_failed = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/credit_app_successful.xml'), 'r') as f:
    credit_app_successful = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/credit_app_missing_ssn.xml'), 'r') as f:
    credit_app_missing_ssn = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/credit_app_invalid_ssn.xml'), 'r') as f:
    credit_app_invalid_ssn = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/credit_app_denied.xml'), 'r') as f:
    credit_app_denied = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/credit_app_pending.xml'), 'r') as f:
    credit_app_pending = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/cybersource_accept.xml'), 'r') as f:
    cybersource_accept = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/cybersource_review.xml'), 'r') as f:
    cybersource_review = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/cybersource_reject.xml'), 'r') as f:
    cybersource_reject = f.read().encode('utf8')
