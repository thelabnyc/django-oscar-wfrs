from decimal import ROUND_UP
from .models import FinancingPlanBenefit


def list_plans_for_basket(basket):
    plans = []
    for application in basket.offer_applications.post_order_actions:
        benefit = application['offer'].benefit.proxy()
        if isinstance(benefit, FinancingPlanBenefit):
            plans += benefit.plans.all()
    plans = { p.pk: p for p in plans }.values()
    plans = sorted(plans, key=lambda plan: '%s-%s' % (plan.apr, plan.term_months))
    return plans


def calculate_monthly_payments(principal, term_months, apr):
    # If the loan term is 0, the payment is the full principal
    if term_months == 0:
        return principal

    # If the APR is 0, just divide the principal by the loan term
    if apr == 0:
        return principal / term_months

    # Convert the APR into a per-month interest rate decimal
    interest = (apr / 100 / 12)

    # Calculate the amortized monthly payment for the loan
    payment = principal * (interest * (1 + interest) ** term_months) / ((1 + interest) ** term_months - 1)

    return payment.quantize(principal, rounding=ROUND_UP)
