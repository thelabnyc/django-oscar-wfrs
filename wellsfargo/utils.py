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
