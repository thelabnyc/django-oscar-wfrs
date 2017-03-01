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


with open(os.path.join(_base, 'responses/credit_app_successful.xml'), 'r') as f:
    credit_app_successful = f.read().encode('utf8')


with open(os.path.join(_base, 'responses/credit_app_invalid_ssn.xml'), 'r') as f:
    credit_app_invalid_ssn = f.read().encode('utf8')


with open(os.path.join(_base, 'responses/credit_app_denied.xml'), 'r') as f:
    credit_app_denied = f.read().encode('utf8')
