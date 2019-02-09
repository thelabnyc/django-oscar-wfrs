from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags
from django.views import generic
from django_tables2 import SingleTableView
from oscar.core.compat import UnicodeCSVWriter
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from ..connector import actions
from ..core.exceptions import CreditApplicationPending, CreditApplicationDenied
from ..core.constants import get_credit_app_status_name, get_prequal_trans_status_name
from ..models import (
    FinancingPlan,
    FinancingPlanBenefit,
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
    TransferMetadata,
    PreQualificationRequest,
)
from .forms import (
    ApplicationSelectionForm,
    FinancingPlanForm,
    FinancingPlanBenefitForm,
    ApplicationSearchForm,
    PreQualSearchForm,
    get_application_form_class,
)
from .tables import CreditApplicationIndexTable, TransferMetadataIndexTable, PreQualificationIndexTable


DEFAULT_APPLICATION = USCreditApp
APPLICATION_MODELS = {
    USCreditApp.APP_TYPE_CODE: USCreditApp,
    USJointCreditApp.APP_TYPE_CODE: USJointCreditApp,
    CACreditApp.APP_TYPE_CODE: CACreditApp,
    CAJointCreditApp.APP_TYPE_CODE: CAJointCreditApp,
}


class CSVDownloadableTableMixin(object):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        download_params = { k: v for k, v in self.request.GET.items() }
        download_params['response_format'] = 'csv'
        context['download_querystring'] = urlencode(download_params)
        return context


    def is_csv_download(self):
        return self.request.GET.get('response_format', None) == 'csv'


    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_download():
            return self.download_applications(self.request, context[self.context_table_name])
        return super().render_to_response(context, **response_kwargs)


    def get_download_filename(self, request):
        return 'results.csv'


    def download_applications(self, request, table):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % self.get_download_filename(request)
        writer = UnicodeCSVWriter(open_file=response)

        def format_csv_cell(str_in):
            if not str_in:
                return '–'
            return strip_tags(str_in).replace('\n', '').strip()

        # Loop through each row in the table, strip out any HTMl, and write it to a CSV excluding the last column (actions).
        for row_raw in table.as_values():
            row_values = tuple(format_csv_cell(value) for value in row_raw)
            writer.writerow(row_values[:-1])

        return response



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
    success_url = reverse_lazy('wfrs-application-list')


    def get(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        return super().get(request, region, language, app_type)


    def post(self, request, region, language, app_type):
        self._init_form(region, language, app_type)
        form = self.get_form()
        if form.is_valid():
            # Save application
            app = form.save()
            app.submitting_user = request.user
            app.save()

            # Submit application
            try:
                result = actions.submit_credit_application(app, current_user=request.user)
                # Update resulting account number
                app.account_number = result.account_number
                app.save()
                return self.form_valid(app)
            except CreditApplicationPending:
                messages.add_message(request, messages.ERROR, _('Credit Application approval is pending'))
                return self.form_valid()
            except CreditApplicationDenied:
                messages.add_message(request, messages.ERROR, _('Credit Application was denied by Wells Fargo'))
            except ValidationError as e:
                messages.add_message(request, messages.ERROR, e.message)
        return self.form_invalid(form)


    def form_valid(self, application=None):
        if application:
            url = reverse('wfrs-application-detail', args=(application.APP_TYPE_CODE, application.pk))
        else:
            url = reverse('wfrs-application-list')
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



class CreditApplicationListView(CSVDownloadableTableMixin, SingleTableView):
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
        status = data.get('status')
        if status:
            qs = qs.filter(status=status)
            self.filter_descrs.append(_('Status is “{status}”').format(status=get_credit_app_status_name(status)))

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


    def get_download_filename(self, request):
        return 'applications.csv'



class CreditApplicationDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/application_detail.html"

    def get_queryset(self):
        app_type = self.kwargs.get('app_type')
        return APPLICATION_MODELS.get(app_type, DEFAULT_APPLICATION).objects.all()



class TransferMetadataListView(SingleTableView):
    template_name = "wfrs/dashboard/transfer_list.html"
    table_class = TransferMetadataIndexTable
    context_table_name = 'transfers'

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = _('Transfers')
        return table

    def get_queryset(self):
        qs = SearchQuerySet().models(TransferMetadata)
        # Default ordering
        if not self.request.GET.get('sort'):
            qs = qs.order_by('-created_datetime')
        return qs



class TransferMetadataDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/transfer_detail.html"
    slug_field = 'merchant_reference'
    slug_url_kwarg = 'merchant_reference'

    def get_queryset(self):
        return TransferMetadata.objects.all()



class PreQualificationListView(CSVDownloadableTableMixin, SingleTableView):
    template_name = "wfrs/dashboard/prequal_list.html"
    form_class = PreQualSearchForm
    table_class = PreQualificationIndexTable
    context_table_name = 'prequal_requests'
    filter_descrs = []


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['search_filters'] = self.filter_descrs
        return context


    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _('Pre-Qualification Search Results')
        return _('Pre-Qualification Requests')


    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table


    def get_queryset(self):
        qs = SearchQuerySet().models(PreQualificationRequest)
        # Default ordering
        if not self.request.GET.get('sort'):
            qs = qs.order_by('-created_datetime', '-id')
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
            self.filter_descrs.append(_('Request contains “{text}”').format(text=search_text))

        # Advanced Search
        customer_initiated = data.get('customer_initiated')
        if customer_initiated is not None:
            qs = qs.filter(customer_initiated__exact=str(customer_initiated).lower())
            self.filter_descrs.append(_('Customer Initiated is “{text}”').format(text=customer_initiated))

        first_name = data.get('first_name')
        if first_name:
            qs = qs.filter(first_name__fuzzy=first_name)
            self.filter_descrs.append(_('First name is “{text}”').format(text=first_name))

        last_name = data.get('last_name')
        if last_name:
            qs = qs.filter(last_name__fuzzy=last_name)
            self.filter_descrs.append(_('Last name is “{text}”').format(text=last_name))

        status = data.get('status')
        if status:
            qs = qs.filter(response_status=status)
            self.filter_descrs.append(_('Status is “{text}”').format(text=get_prequal_trans_status_name(status)))

        created_date_from = data.get('created_date_from')
        if created_date_from:
            qs = qs.filter(created_datetime__gte=created_date_from)
            self.filter_descrs.append(_('Created after {text}').format(text=created_date_from))

        created_date_to = data.get('created_date_to')
        if created_date_to:
            qs = qs.filter(created_datetime__lte=created_date_to)
            self.filter_descrs.append(_('Created before {text}').format(text=created_date_to))

        return qs


    def get_download_filename(self, request):
        return 'prequalifications.csv'



class PreQualificationDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/prequal_detail.html"
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return PreQualificationRequest.objects.all()
