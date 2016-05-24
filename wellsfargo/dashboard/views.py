from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView
from oscar.core.loading import get_model
from oscar_accounts.core import redemptions_account
from .forms import SubmitTransactionForm, ApplicationSelectionForm, get_application_form_class
from ..connector import actions
from ..core.exceptions import CreditApplicationDenied, TransactionDenied

Account = get_model('oscar_accounts', 'Account')



class SubmitTransactionView(FormView):
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
                actions.submit_transaction( form.save(commit=False) )
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
            'user': self.request.user.id,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Submit New Transaction (Wells Fargo)')
        context['account'] = self.account
        return context

    def _init_form(self, source_id):
        self.account = get_object_or_404(Account, pk=source_id)



class ApplicationSelectionView(FormView):
    template_name = 'wfrs/dashboard/select_application.html'
    form_class = ApplicationSelectionForm

    def form_valid(self, form):
        url = reverse('wfrs-apply-step2', kwargs=form.cleaned_data)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Apply for a Credit Line (Wells Fargo)')
        return context



class CreditApplicationView(FormView):
    success_url = reverse_lazy('accounts-list')

    def get(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        return super().get(request, region, language, app_type)

    def post(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        form = self.get_form()
        if form.is_valid():
            try:
                app = form.save(commit=False)
                resp = actions.submit_credit_application(app)
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
