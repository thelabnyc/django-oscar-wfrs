from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, TemplateColumn, DateTimeColumn, LinkColumn, A
from oscar.apps.dashboard.tables import DashboardTable as BaseDashboardTable
import pytz


class TZAwareDateTimeColumn(DateTimeColumn):
    def render(self, record, table, value, bound_column, **kwargs):
        if value and not value.tzinfo:
            value = pytz.utc.localize(value)
        return super().render(record, table, value, bound_column, **kwargs)



class DashboardTable(BaseDashboardTable):
    class Meta(BaseDashboardTable.Meta):
        template_name = 'wfrs/dashboard/responsive-table.html'



class CreditApplicationTable(DashboardTable):
    main_applicant_name = TemplateColumn(
        verbose_name=_('Main Applicant Name'),
        template_name='wfrs/dashboard/_application_row_main_applicant_name.html',
        order_by=('main_applicant__last_name', 'main_applicant__first_name'))
    secondary_applicant_name = TemplateColumn(
        verbose_name=_('Secondary Applicant Name'),
        template_name='wfrs/dashboard/_application_row_secondary_applicant_name.html',
        order_by=('joint_applicant__last_name', 'joint_applicant__first_name'))
    application_type = TemplateColumn(
        verbose_name=_('Application Type'),
        template_name='wfrs/dashboard/_application_row_type.html',
        orderable=False)
    merchant_name = Column(
        verbose_name=_('Merchant Name'),
        orderable=False)
    application_source = Column(
        verbose_name=_('Application Source'),
        orderable=False)
    user = TemplateColumn(
        verbose_name=_('Owner'),
        template_name='wfrs/dashboard/_application_row_user.html',
        order_by=('user__last_name', 'user__first_name', 'user__username'))
    submitting_user = TemplateColumn(
        verbose_name=_('Submitted By'),
        template_name='wfrs/dashboard/_application_row_submitting_user.html',
        order_by=('submitting_user__first_name', 'submitting_user__last_name', 'submitting_user__username'))
    status = Column(
        verbose_name=_('Application Status'),
        orderable=False)
    account_number = TemplateColumn(
        verbose_name=_('Resulting Account Number'),
        template_name='wfrs/dashboard/_application_row_account_number.html',
        order_by='last4_account_number')
    purchase_price = TemplateColumn(
        verbose_name=_('Requested Value'),
        template_name='wfrs/dashboard/_application_row_purchase_price.html',
        orderable=False)
    credit_limit = TemplateColumn(
        verbose_name=_('Credit Limit'),
        template_name='wfrs/dashboard/_application_row_credit_limit.html',
        orderable=False)
    order_total = TemplateColumn(
        verbose_name=_('Order Total'),
        template_name='wfrs/dashboard/_application_row_order_total.html',
        orderable=False)
    order_delay = TemplateColumn(
        verbose_name=_('Time until Order Placement (Minutes)'),
        template_name='wfrs/dashboard/_application_row_order_delay.html',
        orderable=False)
    order_merchant_name = TemplateColumn(
        verbose_name=_('Order Merchant Name'),
        template_name='wfrs/dashboard/_application_row_order_merchant_name.html',
        orderable=False)
    created_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Created On'),
        order_by='created_datetime',
        format='D, N j Y, P')
    modified_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Last Modified On'),
        order_by='modified_datetime',
        format='D, N j Y, P')
    actions = TemplateColumn(
        verbose_name=_('Actions'),
        template_name='wfrs/dashboard/_application_row_actions.html',
        orderable=False)

    class Meta(DashboardTable.Meta):
        sequence = (
            'main_applicant_name',
            'secondary_applicant_name',
            'application_type',
            'merchant_name',
            'application_source',
            'user',
            'submitting_user',
            'status',
            'account_number',
            'purchase_price',
            'credit_limit',
            'order_total',
            'order_delay',
            'order_merchant_name',
            'created_datetime',
            'modified_datetime',
            'actions'
        )



class TransferMetadataTable(DashboardTable):
    merchant_reference = LinkColumn('wfrs-transfer-detail',
        args=[A('merchant_reference')])
    masked_account_number = Column(
        verbose_name=_('Account Number'),
        order_by=('last4_account_number'))
    order = TemplateColumn(
        verbose_name=_('Order'),
        template_name='wfrs/dashboard/_transfer_row_order.html',
        orderable=False)
    user = TemplateColumn(
        verbose_name=_('User'),
        template_name='wfrs/dashboard/_transfer_row_user.html',
        order_by=('user__last_name', 'user__first_name', 'user__username'))
    amount = Column(
        verbose_name=_('Amount'))
    type_name = Column(
        verbose_name=_('Type'),
        order_by=('type_code', ))
    ticket_number = Column(
        verbose_name=_('Ticket Number'))
    financing_plan_number = Column(
        verbose_name=_('Plan Number'),
        order_by=('financing_plan__plan_number', ))
    auth_number = Column(
        verbose_name=_('Authorization Number'))
    created_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Created On'),
        order_by='created_datetime',
        format='D, N j Y, P')

    class Meta(DashboardTable.Meta):
        sequence = (
            'merchant_reference',
            'masked_account_number',
            'order',
            'user',
            'amount',
            'type_name',
            'ticket_number',
            'financing_plan_number',
            'auth_number',
            'created_datetime',
        )



class PreQualificationTable(DashboardTable):
    uuid = LinkColumn('wfrs-prequal-detail',
        args=[A('uuid')],
        verbose_name=_('UUID'),
        orderable=False)
    merchant_name = Column(
        verbose_name=_('Merchant Name'),
        accessor=A('merchant_name'),
        orderable=False)
    first_name = Column(
        verbose_name=_('First Name'),
        orderable=False)
    last_name = Column(
        verbose_name=_('Last Name'),
        orderable=False)
    address = TemplateColumn(
        verbose_name=_('Address'),
        template_name='wfrs/dashboard/_prequal_row_address.html',
        orderable=False)
    status_name = Column(
        verbose_name=_('Status'),
        orderable=False)
    credit_limit = TemplateColumn(
        verbose_name=_('Pre-Qual Credit Limit'),
        template_name='wfrs/dashboard/_prequal_row_credit_limit.html',
        orderable=False)
    customer_response = Column(
        verbose_name=_('Customer Response'),
        orderable=False)
    sdk_application_result = Column(
        verbose_name=_('SDK Application Result'),
        orderable=False)
    merchant_num = Column(
        verbose_name=_('Merchant Number'),
        orderable=False)
    customer_initiated = Column(
        verbose_name=_('Customer Initiated'),
        orderable=False)
    order_total = TemplateColumn(
        verbose_name=_('Order Total'),
        template_name='wfrs/dashboard/_prequal_row_order_total.html',
        orderable=False)
    order_delay = TemplateColumn(
        verbose_name=_('Time until Order Placement (Minutes)'),
        template_name='wfrs/dashboard/_prequal_row_order_delay.html',
        orderable=False)
    order_merchant_name = Column(
        verbose_name=_('Order Merchant Name'),
        orderable=False)
    created_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Created On'),
        order_by='created_datetime',
        format='D, N j Y, P')
    response_reported_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Reported On'),
        order_by='response__reported_datetime',
        format='D, N j Y, P')

    class Meta(DashboardTable.Meta):
        sequence = (
            'uuid',
            'merchant_name',
            'first_name',
            'last_name',
            'address',
            'status_name',
            'credit_limit',
            'customer_response',
            'sdk_application_result',
            'merchant_num',
            'customer_initiated',
            'order_total',
            'order_delay',
            'order_merchant_name',
            'created_datetime',
            'response_reported_datetime',
        )



class SDKApplicationTable(DashboardTable):
    application_id = Column(
        verbose_name=_('Application ID'),
        orderable=False)
    first_name = Column(
        verbose_name=_('First Name'),
        orderable=False)
    last_name = Column(
        verbose_name=_('Last Name'),
        orderable=False)
    application_status = Column(
        verbose_name=_('Status'),
        orderable=False)
    prequal_details = TemplateColumn(
        verbose_name=_('Pre-Qualification Details'),
        template_name='wfrs/dashboard/_sdk_application_row_prequal_link.html',
        orderable=False)
    created_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Created On'),
        order_by='created_datetime',
        format='D, N j Y, P')
    modified_datetime = TZAwareDateTimeColumn(
        verbose_name=_('Last Modified On'),
        order_by='modified_datetime',
        format='D, N j Y, P')

    class Meta(DashboardTable.Meta):
        sequence = (
            'application_id',
            'first_name',
            'last_name',
            'application_status',
            'prequal_details',
            'created_datetime',
            'modified_datetime',
        )
