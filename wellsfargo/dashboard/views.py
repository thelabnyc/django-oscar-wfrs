from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django_tables2 import SingleTableView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from oscar.core.loading import get_model
from oscar_accounts.core import redemptions_account
from ..connector import actions
from ..core.constants import CREDIT_APP_APPROVED
from ..core.exceptions import CreditApplicationDenied, TransactionDenied
from ..core.structures import CreditApplicationResult
from ..models import (
    FinancingPlan,
    FinancingPlanBenefit,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)
from .forms import (
    SubmitTransactionForm,
    ApplicationSelectionForm,
    ManualAddAccountForm,
    FinancingPlanForm,
    FinancingPlanBenefitForm,
    ApplicationSearchForm,
    get_application_form_class,
)
from .tables import CreditApplicationIndexTable


Account = get_model('oscar_accounts', 'Account')


DEFAULT_APPLICATION = USCreditApp
APPLICATION_MODELS = {
    USCreditApp.APP_TYPE_CODE: USCreditApp,
    USJointCreditApp.APP_TYPE_CODE: USJointCreditApp,
    CACreditApp.APP_TYPE_CODE: CACreditApp,
    CAJointCreditApp.APP_TYPE_CODE: CAJointCreditApp,
}



class SubmitTransactionView(generic.FormView):
    template_name = 'wfrs/dashboard/submit_transaction.html'
    form_class = SubmitTransactionForm

    def get(self, request, source_id):
        self._init_form(source_id)
        return super().get(request, source_id)

    def post(self, request, source_id):
        self._init_form(source_id)
        form = self.get_form()
        if form.is_valid():
            try:
                actions.submit_transaction(form.save(), current_user=request.user)
                return self.form_valid(form)
            except TransactionDenied as e:
                messages.add_message(request, messages.ERROR, _('Transaction was denied by Wells Fargo'))
            except ValidationError as e:
                messages.add_message(request, messages.ERROR, e.message)
        return self.form_invalid(form)

    def form_valid(self, form):
        url = reverse('accounts-detail', args=(self.account.id, ))
        return HttpResponseRedirect(url)

    def get_initial(self):
        return {
            'source_account': self.account.id,
            'dest_account': redemptions_account().id,
            'user': self.account.primary_user.id,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Submit New Transaction (Wells Fargo)')
        context['account'] = self.account
        return context

    def _init_form(self, source_id):
        self.account = get_object_or_404(Account, pk=source_id)



class ApplicationSelectionView(generic.FormView):
    template_name = 'wfrs/dashboard/select_application.html'
    form_class = ApplicationSelectionForm

    def form_valid(self, form):
        url = reverse('wfrs-apply-step2', kwargs=form.cleaned_data)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Apply for a Credit Line (Wells Fargo)')
        return context



class CreditApplicationView(generic.FormView):
    success_url = reverse_lazy('accounts-list')

    def get(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        return super().get(request, region, language, app_type)

    def post(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        form = self.get_form()
        if form.is_valid():
            try:
                app = form.save()
                app.submitting_user = request.user
                app.save()
                resp = actions.submit_credit_application(app, current_user=request.user)
                account = resp.save()
                return self.form_valid(account)
            except CreditApplicationDenied as e:
                messages.add_message(request, messages.ERROR, _('Credit Application was denied by Wells Fargo'))
            except ValidationError as e:
                messages.add_message(request, messages.ERROR, e.message)
        return self.form_invalid(form)

    def form_valid(self, account):
        url = reverse('accounts-detail', args=(account.pk, ))
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Apply for a Credit Line (Wells Fargo)')
        return context

    def _init_form(self, region, language, app_type):
        self.initial = {
            'region': region,
            'language': language,
            'app_type': app_type,
        }
        self.form_class = get_application_form_class(region, app_type)
        self.template_name = self.form_class.dashboard_template



class AddExistingAccountView(generic.FormView):
    form_class = ManualAddAccountForm
    template_name = 'wfrs/dashboard/add_account.html'

    def form_valid(self, form):
        struct = CreditApplicationResult()
        struct.transaction_status = CREDIT_APP_APPROVED
        struct.account_number = form.cleaned_data['account_number']
        struct.credit_limit = form.cleaned_data['credit_limit']
        account = struct.save(
            owner=form.cleaned_data['primary_user'],
            status=form.cleaned_data['status'],
            name=form.cleaned_data['name'],
            locale=form.cleaned_data['locale'],
            billing_address={
                'title': form.cleaned_data['title'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'line1': form.cleaned_data['line1'],
                'line2': form.cleaned_data['line2'],
                'line3': form.cleaned_data['line3'],
                'line4': form.cleaned_data['line4'],
                'state': form.cleaned_data['state'],
                'postcode': form.cleaned_data['postcode'],
                'country': form.cleaned_data['country'],
            })

        url = reverse('accounts-detail', kwargs={'pk': account.pk})
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Existing Wells Fargo Account')
        return context


class FinancingPlanListView(generic.ListView):
    model = FinancingPlan
    template_name = "wfrs/dashboard/plan_list.html"
    context_object_name = "plans"


class FinancingPlanCreateView(generic.CreateView):
    model = FinancingPlan
    form_class = FinancingPlanForm
    template_name = "wfrs/dashboard/plan_form.html"
    success_url = reverse_lazy('wfrs-plan-list')
    context_object_name = "plan"


class FinancingPlanUpdateView(generic.UpdateView):
    model = FinancingPlan
    form_class = FinancingPlanForm
    template_name = "wfrs/dashboard/plan_form.html"
    success_url = reverse_lazy('wfrs-plan-list')
    context_object_name = "plan"


class FinancingPlanDeleteView(generic.DeleteView):
    model = FinancingPlan
    template_name = "wfrs/dashboard/plan_delete.html"
    success_url = reverse_lazy('wfrs-plan-list')
    context_object_name = "plan"


class FinancingPlanBenefitListView(generic.ListView):
    model = FinancingPlanBenefit
    template_name = "wfrs/dashboard/benefit_list.html"
    context_object_name = "benefits"


class FinancingPlanBenefitCreateView(generic.CreateView):
    model = FinancingPlanBenefit
    form_class = FinancingPlanBenefitForm
    template_name = "wfrs/dashboard/benefit_form.html"
    success_url = reverse_lazy('wfrs-benefit-list')
    context_object_name = "benefit"


class FinancingPlanBenefitUpdateView(generic.UpdateView):
    model = FinancingPlanBenefit
    form_class = FinancingPlanBenefitForm
    template_name = "wfrs/dashboard/benefit_form.html"
    success_url = reverse_lazy('wfrs-benefit-list')
    context_object_name = "benefit"


class FinancingPlanBenefitDeleteView(generic.DeleteView):
    model = FinancingPlanBenefit
    template_name = "wfrs/dashboard/benefit_delete.html"
    success_url = reverse_lazy('wfrs-benefit-list')
    context_object_name = "benefit"


class CreditApplicationListView(SingleTableView):
    template_name = "wfrs/dashboard/application_list.html"
    form_class = ApplicationSearchForm
    table_class = CreditApplicationIndexTable
    context_table_name = 'applications'
    filter_descrs = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['search_filters'] = self.filter_descrs
        return context

    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _('Credit Application Search Results')
        return _('Credit Applications')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table

    def get_queryset(self):
        qs = SearchQuerySet().models(*APPLICATION_MODELS.values())
        # Default ordering
        if not self.request.GET.get('sort'):
            qs = qs.order_by('-created_datetime')
        # Apply search filters
        qs = self.apply_search(qs)
        return qs

    def apply_search(self, qs):
        self.filter_descrs = []
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs
        data = self.form.cleaned_data

        # Basic search
        search_text = data.get('search_text')
        if search_text:
            qs = qs.filter(text=AutoQuery(search_text))
            self.filter_descrs.append(_('Application contains “{text}”').format(text=search_text))

        # Advanced search
        name = data.get('name')
        if name:
            qs = qs.filter(name=name)
            self.filter_descrs.append(_('Applicant name contains “{name}”').format(name=name))

        email = data.get('email')
        if email:
            qs = qs.filter(email=email)
            self.filter_descrs.append(_('Applicant email contains “{email}”').format(email=email))

        address = data.get('address')
        if address:
            qs = qs.filter(address=address)
            self.filter_descrs.append(_('Applicant address contains “{address}”').format(address=address))

        phone = data.get('phone')
        if phone:
            qs = qs.filter(phone__exact=phone)
            self.filter_descrs.append(_('Phone number contains “{phone}”').format(phone=phone))

        created_date_from = data.get('created_date_from')
        if created_date_from:
            qs = qs.filter(created_datetime__gt=created_date_from)
            self.filter_descrs.append(_('Application submitted after {date}').format(date=created_date_from.strftime('%c')))

        created_date_to = data.get('created_date_to')
        if created_date_to:
            qs = qs.filter(created_datetime__lt=created_date_to)
            self.filter_descrs.append(_('Application submitted before {date}').format(date=created_date_to.strftime('%c')))

        submitted_by = data.get('submitted_by')

        user_id = data.get('user_id')
        if user_id:
            user = get_object_or_404(get_user_model(), pk=user_id)
            qs = qs.filter(user_id=user_id)
            self.filter_descrs.append(_('Application owned by “{name}”').format(name=user.get_full_name()))

        submitting_user_id = data.get('submitting_user_id')
        submitted_by = data.get('submitted_by')
        if submitting_user_id:
            user = get_object_or_404(get_user_model(), pk=submitting_user_id)
            qs = qs.filter(submitting_user_id=submitting_user_id)
            self.filter_descrs.append(_('Application submitted by “{name}”').format(name=user.get_full_name()))
        elif submitted_by:
            qs = qs.filter(submitting_user_full_name=submitted_by)
            self.filter_descrs.append(_('Application submitted by “{name}”').format(name=submitted_by))

        return qs


class CreditApplicationDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/application_detail.html"

    def get_queryset(self):
        app_type = self.kwargs.get('app_type')
        return APPLICATION_MODELS.get(app_type, DEFAULT_APPLICATION).objects.all()
