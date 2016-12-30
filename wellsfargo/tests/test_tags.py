from django.test import TestCase
from django.template import Context, Template
from ..models import FinancingPlan


class TestDefaultPlanTag(TestCase):
    def render_template(self, string, context=None):
        context = context or {}
        context = Context(context)
        return Template(string).render(context)

    def test_wfrs_default_plan(self):
        """ Render a simple template with the default tag,
        show the financing plan appears
        """
        FinancingPlan.objects.create(
            plan_number=1,
            is_default_plan=False
        )
        FinancingPlan.objects.create(
            plan_number=2,
            is_default_plan=True
        )
        rendered = self.render_template(
            '{% load wfrs_default_plan %}'
            '{% get_default_plan as default_plan %}'
            '{{ default_plan }}'
        )
        self.assertIn('2', rendered)


class TestRequiresCreditLineTag(TestCase):
    def render_template(self, string, context=None):
        context = context or {}
        context = Context(context)
        return Template(string).render(context)

    def test_wfrs_requires_credit_line(self):
        """ Render a simple template with the requires_credit_line tag,
        show the financing plan appears
        """
        FinancingPlan.objects.create(
            plan_number=1,
            requires_credit_line=False
        )
        FinancingPlan.objects.create(
            plan_number=2,
            requires_credit_line=True
        )
        rendered = self.render_template(
            '{% load wfrs_requires_credit_line %}'
            '{% get_requires_credit_line as requires_credit_line %}'
            '{{ requires_credit_line }}'
        )
        self.assertIn('2', rendered)
