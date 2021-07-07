from decimal import Decimal
from django.test import TestCase
from wellsfargo.models import FinancingPlan
from wellsfargo.dashboard.forms import (
    FinancingPlanForm,
    FinancingPlanBenefitForm,
)


class FinancingPlanFormTest(TestCase):
    def test_create(self):
        form = FinancingPlanForm(
            data={
                "plan_number": 9999,
                "description": "Foo Bar",
                "apr": "27.99",
                "term_months": 0,
                "is_default_plan": True,
                "product_price_threshold": "0.00",
                "allow_credit_application": True,
            }
        )

        self.assertTrue(form.is_valid())

        plan = form.save()
        self.assertEqual(plan.plan_number, 9999)
        self.assertEqual(plan.description, "Foo Bar")
        self.assertEqual(plan.apr, Decimal("27.99"))
        self.assertEqual(plan.term_months, 0)
        self.assertEqual(plan.is_default_plan, True)
        self.assertEqual(plan.allow_credit_application, True)

    def test_update(self):
        plan1 = FinancingPlan()
        plan1.plan_number = 9999
        plan1.description = "Foo Bar"
        plan1.apr = "27.99"
        plan1.term_months = 0
        plan1.is_default_plan = True
        plan1.allow_credit_application = True
        plan1.save()

        form = FinancingPlanForm(
            instance=plan1,
            data={
                "plan_number": 9999,
                "description": "Foo Bar",
                "apr": "10.50",
                "term_months": 0,
                "is_default_plan": True,
                "product_price_threshold": "0.00",
                "allow_credit_application": True,
            },
        )

        self.assertTrue(form.is_valid())

        plan2 = form.save()
        self.assertEqual(plan2.pk, plan1.pk)
        self.assertEqual(plan2.plan_number, 9999)
        self.assertEqual(plan2.description, "Foo Bar")
        self.assertEqual(plan2.apr, Decimal("10.50"))
        self.assertEqual(plan2.term_months, 0)
        self.assertEqual(plan2.is_default_plan, True)
        self.assertEqual(plan2.allow_credit_application, True)


class FinancingPlanBenefitFormTest(TestCase):
    def setUp(self):
        self.plan = FinancingPlan.objects.create(
            plan_number=9999,
            description="Foo Bar",
            apr="27.99",
            term_months=0,
            is_default_plan=True,
            allow_credit_application=True,
        )

    def test_create(self):
        form = FinancingPlanBenefitForm(
            data={
                "group_name": "Default Group",
                "plans": (self.plan.pk,),
            }
        )

        self.assertTrue(form.is_valid())

        benefit = form.save()
        self.assertEqual(benefit.proxy_class, "wellsfargo.models.FinancingPlanBenefit")
        self.assertEqual(benefit.group_name, "Default Group")
        self.assertEqual(benefit.plans.count(), 1)
        self.assertEqual(benefit.plans.first(), self.plan)
