from django.utils.translation import ugettext_lazy as _
from django_tables2 import Column, TemplateColumn, DateTimeColumn, LinkColumn, A
from oscar.core.loading import get_class
import pytz

DashboardTable = get_class('dashboard.tables', 'DashboardTable')


class TZAwareDateTimeColumn(DateTimeColumn):
    def render(self, record, table, value, bound_column, **kwargs):
        value = pytz.utc.localize(value)
        return super().render(record, table, value, bound_column, **kwargs)


class CreditApplicationIndexTable(DashboardTable):
    main_applicant_name = TemplateColumn(
        verbose_name=_('Main Applicant Name'),
        template_name='wfrs/dashboard/_application_row_main_applicant_name.html',
        order_by=('main_last_name', 'main_first_name'))
    secondary_applicant_name = TemplateColumn(
        verbose_name=_('Secondary Applicant Name'),
        template_name='wfrs/dashboard/_application_row_secondary_applicant_name.html',
        order_by=('joint_last_name', 'joint_first_name'))
    application_type = TemplateColumn(
        verbose_name=_('Application Type'),
        template_name='wfrs/dashboard/_application_row_type.html',
        orderable=False)
    user = TemplateColumn(
        verbose_name=_('Owner'),
        template_name='wfrs/dashboard/_application_row_user.html',
        order_by=('user_full_name', 'user_username'))
    submitting_user = TemplateColumn(
        verbose_name=_('Submitted By'),
        template_name='wfrs/dashboard/_application_row_submitting_user.html',
        order_by=('submitting_user_full_name', 'submitting_user_username'))
    account_number = TemplateColumn(
        verbose_name=_('Resulting Account Number'),
        template_name='wfrs/dashboard/_application_row_account_number.html',
        order_by='account_number')
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
            'user',
            'submitting_user',
            'account_number',
            'created_datetime',
            'modified_datetime',
            'actions'
        )



class TransferMetadataIndexTable(DashboardTable):
    merchant_reference = LinkColumn('wfrs-transfer-detail', args=[A('merchant_reference')])
    masked_account_number = Column(verbose_name=_('Account Number'))
    order = TemplateColumn(
        verbose_name=_('Order'),
        template_name='wfrs/dashboard/_transfer_row_order.html',
        order_by='order_number')
    user = TemplateColumn(
        verbose_name=_('User'),
        template_name='wfrs/dashboard/_transfer_row_user.html',
        order_by=('user_full_name', 'user_username'))
    amount = Column(verbose_name=_('Amount'))
    type_code_name = Column(verbose_name=_('Type'))
    ticket_number = Column(verbose_name=_('Ticket Number'))
    financing_plan_number = Column(verbose_name=_('Plan Number'))
    auth_number = Column(verbose_name=_('Authorization Number'))
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
            'type_code_name',
            'ticket_number',
            'financing_plan_number',
            'auth_number',
            'created_datetime',
        )
