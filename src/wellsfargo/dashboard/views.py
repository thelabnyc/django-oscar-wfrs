from urllib.parse import urlencode
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVector
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils.html import strip_tags
from django.views import generic
from django_tables2 import SingleTableView
from oscar.core.compat import UnicodeCSVWriter
from ..core.constants import (
    get_prequal_trans_status_name,
    PREQUAL_TRANS_STATUS_REJECTED,
)
from ..models import (
    FinancingPlan,
    FinancingPlanBenefit,
    CreditApplication,
    TransferMetadata,
    PreQualificationRequest,
    PreQualificationSDKApplicationResult,
)
from .forms import (
    FinancingPlanForm,
    FinancingPlanBenefitForm,
    ApplicationSearchForm,
    PreQualSearchForm,
    SDKApplicationSearchForm,
)
from .tables import (
    CreditApplicationTable,
    TransferMetadataTable,
    PreQualificationTable,
    SDKApplicationTable,
)


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
    table_class = CreditApplicationTable
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
        qs = CreditApplication.objects.get_queryset()
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
            qs = qs\
                .annotate(
                    text=SearchVector(
                        'main_applicant__first_name',
                        'main_applicant__last_name',
                        'joint_applicant__first_name',
                        'joint_applicant__last_name',
                        'main_applicant__email_address',
                        'joint_applicant__email_address',
                        'main_applicant__address__address_line_1',
                        'main_applicant__address__address_line_2',
                        'main_applicant__address__city',
                        'main_applicant__address__state_code',
                        'main_applicant__address__postal_code',
                        'joint_applicant__address__address_line_1',
                        'joint_applicant__address__address_line_2',
                        'joint_applicant__address__city',
                        'joint_applicant__address__state_code',
                        'joint_applicant__address__postal_code',
                        'main_applicant__home_phone',
                        'main_applicant__mobile_phone',
                        'main_applicant__work_phone',
                        'joint_applicant__home_phone',
                        'joint_applicant__mobile_phone',
                        'joint_applicant__work_phone',
                    ),
                )\
                .filter(text=search_text)
            self.filter_descrs.append(_('Application contains “%(text)s”') % dict(text=search_text))

        # Advanced search
        status = data.get('status')
        if status:
            qs = qs.filter(status=status)
            self.filter_descrs.append(_('Status is “%(status)s”') % dict(status=status))

        name = data.get('name')
        if name:
            qs = qs\
                .annotate(
                    name=SearchVector(
                        'main_applicant__first_name',
                        'main_applicant__last_name',
                        'joint_applicant__first_name',
                        'joint_applicant__last_name',
                    ),
                )\
                .filter(name=name)
            self.filter_descrs.append(_('Applicant name contains “%(name)s”') % dict(name=name))

        email = data.get('email')
        if email:
            qs = qs\
                .annotate(
                    email=SearchVector(
                        'main_applicant__email_address',
                        'joint_applicant__email_address',
                    ),
                )\
                .filter(email=email)
            self.filter_descrs.append(_('Applicant email contains “%(email)s”') % dict(email=email))

        address = data.get('address')
        if address:
            qs = qs\
                .annotate(
                    addr=SearchVector(
                        'main_applicant__address__address_line_1',
                        'main_applicant__address__address_line_2',
                        'main_applicant__address__city',
                        'main_applicant__address__state_code',
                        'main_applicant__address__postal_code',
                        'joint_applicant__address__address_line_1',
                        'joint_applicant__address__address_line_2',
                        'joint_applicant__address__city',
                        'joint_applicant__address__state_code',
                        'joint_applicant__address__postal_code',
                    ),
                )\
                .filter(addr=address)
            self.filter_descrs.append(_('Applicant address contains “%(address)s”') % dict(address=address))

        phone = data.get('phone')
        if phone:
            qs = qs\
                .annotate(
                    phone=SearchVector(
                        'main_applicant__home_phone',
                        'main_applicant__mobile_phone',
                        'main_applicant__work_phone',
                        'joint_applicant__home_phone',
                        'joint_applicant__mobile_phone',
                        'joint_applicant__work_phone',
                    ),
                )\
                .filter(phone=phone)
            self.filter_descrs.append(_('Phone number contains “%(phone)s”') % dict(phone=phone))

        created_date_from = data.get('created_date_from')
        if created_date_from:
            qs = qs.filter(created_datetime__gt=created_date_from)
            self.filter_descrs.append(_('Application submitted after %(date)s') % dict(date=created_date_from.strftime('%c')))

        created_date_to = data.get('created_date_to')
        if created_date_to:
            qs = qs.filter(created_datetime__lt=created_date_to)
            self.filter_descrs.append(_('Application submitted before %(date)s') % dict(date=created_date_to.strftime('%c')))

        user_id = data.get('user_id')
        if user_id:
            user = get_object_or_404(get_user_model(), pk=user_id)
            qs = qs.filter(user_id=user_id)
            self.filter_descrs.append(_('Application owned by “%(name)s”') % dict(name=user.get_full_name()))

        submitting_user_id = data.get('submitting_user_id')
        submitted_by = data.get('submitted_by')
        if submitting_user_id:
            user = get_object_or_404(get_user_model(), pk=submitting_user_id)
            qs = qs.filter(submitting_user=user)
            self.filter_descrs.append(_('Application submitted by “%(name)s”') % dict(name=user.get_full_name()))
        elif submitted_by:
            qs = qs\
                .annotate(
                    submitting_user_name=SearchVector(
                        'submitting_user__first_name',
                        'submitting_user__last_name',
                    ),
                )\
                .filter(submitting_user_name=submitted_by)
            self.filter_descrs.append(_('Application submitted by “%(name)s”') % dict(name=submitted_by))

        return qs


    def get_download_filename(self, request):
        return 'applications.csv'



class CreditApplicationDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/application_detail.html"
    queryset = CreditApplication.objects.all()



class TransferMetadataListView(SingleTableView):
    template_name = "wfrs/dashboard/transfer_list.html"
    table_class = TransferMetadataTable
    context_table_name = 'transfers'

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = _('Transfers')
        return table

    def get_queryset(self):
        qs = TransferMetadata.objects.get_queryset()
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
    table_class = PreQualificationTable
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
        qs = PreQualificationRequest.objects.get_queryset()
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
            qs = qs.annotate(text=SearchVector(
                'first_name',
                'last_name',
                'line1',
                'city',
                'state',
                'postcode',
                'phone',
            ))
            qs = qs.filter(text=search_text)
            self.filter_descrs.append(_('Request contains “%(text)s”') % dict(text=search_text))

        # Advanced Search
        customer_initiated = data.get('customer_initiated')
        if customer_initiated is not None:
            qs = qs.filter(customer_initiated=customer_initiated)
            self.filter_descrs.append(_('Customer Initiated is “%(text)s”') % dict(text=customer_initiated))

        first_name = data.get('first_name')
        if first_name:
            qs = qs.filter(first_name__search=first_name)
            self.filter_descrs.append(_('First name is “%(text)s”') % dict(text=first_name))

        last_name = data.get('last_name')
        if last_name:
            qs = qs.filter(last_name__search=last_name)
            self.filter_descrs.append(_('Last name is “%(text)s”') % dict(text=last_name))

        status = data.get('status')
        if status:
            if status == PREQUAL_TRANS_STATUS_REJECTED:
                qs = qs.filter(Q(response__status=status) | Q(response__isnull=True))
            else:
                qs = qs.filter(response__status=status)
            self.filter_descrs.append(_('Status is “%(text)s”') % dict(text=get_prequal_trans_status_name(status)))

        created_date_from = data.get('created_date_from')
        if created_date_from:
            qs = qs.filter(created_datetime__gte=created_date_from)
            self.filter_descrs.append(_('Created after %(text)s') % dict(text=created_date_from))

        created_date_to = data.get('created_date_to')
        if created_date_to:
            qs = qs.filter(created_datetime__lte=created_date_to)
            self.filter_descrs.append(_('Created before %(text)s') % dict(text=created_date_to))

        return qs


    def get_download_filename(self, request):
        return 'prequalifications.csv'



class PreQualificationDetailView(generic.DetailView):
    template_name = "wfrs/dashboard/prequal_detail.html"
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_queryset(self):
        return PreQualificationRequest.objects.all()



class SDKApplicationListView(CSVDownloadableTableMixin, SingleTableView):
    template_name = "wfrs/dashboard/sdk_application_list.html"
    form_class = SDKApplicationSearchForm
    table_class = SDKApplicationTable
    context_table_name = 'applications'
    filter_descrs = []


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        context['search_filters'] = self.filter_descrs
        return context


    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _('SDK Credit Application Search Results')
        return _('SDK Credit Applications')


    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table


    def get_queryset(self):
        qs = PreQualificationSDKApplicationResult.objects.get_queryset()
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
            qs = qs.annotate(text=SearchVector(
                'first_name',
                'last_name',
            ))
            qs = qs.filter(text=search_text)
            self.filter_descrs.append(_('Application contains “%(text)s”') % dict(text=search_text))

        # Advanced Search
        created_date_from = data.get('created_date_from')
        if created_date_from:
            qs = qs.filter(created_datetime__gte=created_date_from)
            self.filter_descrs.append(_('Created after %(text)s') % dict(text=created_date_from))

        created_date_to = data.get('created_date_to')
        if created_date_to:
            qs = qs.filter(created_datetime__lte=created_date_to)
            self.filter_descrs.append(_('Created before %(text)s') % dict(text=created_date_to))

        return qs


    def get_download_filename(self, request):
        return 'sdk-credit-applications.csv'
