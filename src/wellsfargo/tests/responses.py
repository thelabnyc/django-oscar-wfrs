import os.path
_base = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(_base, 'responses/cybersource_accept.xml'), 'r') as f:
    cybersource_accept = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/cybersource_review.xml'), 'r') as f:
    cybersource_review = f.read().encode('utf8')

with open(os.path.join(_base, 'responses/cybersource_reject.xml'), 'r') as f:
    cybersource_reject = f.read().encode('utf8')
