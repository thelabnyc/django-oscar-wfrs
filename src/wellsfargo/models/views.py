from django.conf import settings
from django.db import models, connection
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.fields import citext
from django.utils.functional import cached_property
from django_pgviews.signals import view_synced
from django_pgviews import view as pg
from .apps import (
    USCreditApp,
    USJointCreditApp,
    CACreditApp,
    CAJointCreditApp,
)



def _build_credit_app_query(AppModel, is_joint):
    joint_columns = """
        '' as "joint_first_name",
        '' as "joint_last_name",
    """
    name_vector = """
        a.main_first_name || ' ' ||
        a.main_last_name || ' ' ||
        a.main_middle_initial
    """
    address_vector = """
        a.main_address_line1 || ' ' ||
        a.main_address_line2 || ' ' ||
        a.main_address_city || ' ' ||
        a.main_address_state || ' ' ||
        a.main_address_postcode
    """
    phone_vector = """
        a.main_home_phone || ' ' ||
        a.main_employer_phone || ' ' ||
        a.main_cell_phone
    """
    text_vector = """
        a.email || ' ' ||
        a.main_first_name || ' ' ||
        a.main_middle_initial || ' ' ||
        a.main_last_name || ' ' ||
        a.main_address_line1 || ' ' ||
        a.main_address_line2 || ' ' ||
        a.main_address_city || ' ' ||
        a.main_address_state || ' ' ||
        a.main_address_postcode || ' ' ||
        a.main_home_phone || ' ' ||
        a.main_employer_name || ' ' ||
        a.main_employer_phone || ' ' ||
        a.main_cell_phone || ' ' ||
        a.main_occupation || ' ' ||
        u.first_name || ' ' ||
        u.last_name || ' ' ||
        s.first_name || ' ' ||
        s.last_name
    """
    if is_joint:
        joint_columns = """
            a.joint_first_name as "joint_first_name",
            a.joint_last_name as "joint_last_name",
        """
        name_vector += """ || ' ' ||
            a.joint_first_name || ' ' ||
            a.joint_last_name || ' ' ||
            a.joint_middle_initial
        """
        address_vector += """ || ' ' ||
            a.joint_address_line1 || ' ' ||
            a.joint_address_line2 || ' ' ||
            a.joint_address_city || ' ' ||
            a.joint_address_state || ' ' ||
            a.joint_address_postcode
        """
        phone_vector += """ || ' ' ||
            a.joint_employer_phone || ' ' ||
            a.joint_cell_phone
        """
        text_vector += """ || ' ' ||
            a.joint_first_name || ' ' ||
            a.joint_middle_initial || ' ' ||
            a.joint_last_name || ' ' ||
            a.joint_address_line1 || ' ' ||
            a.joint_address_line2 || ' ' ||
            a.joint_address_city || ' ' ||
            a.joint_address_state || ' ' ||
            a.joint_address_postcode || ' ' ||
            a.joint_employer_name || ' ' ||
            a.joint_employer_phone || ' ' ||
            a.joint_cell_phone || ' ' ||
            a.joint_occupation
        """

    query_template = """
        SELECT '{app_type_code}' as "app_type_code",
               a.id as "id",

               c.name as "merchant_name",
               a.status as "status",
               a.application_source as "application_source",
               a.modified_datetime as "modified_datetime",
               a.created_datetime as "created_datetime",

               (CASE
                WHEN a.last4_account_number IS NULL OR a.last4_account_number = '' THEN ''
                ELSE CONCAT('xxxxxxxxxxxx', a.last4_account_number)
                END) as "account_number",
               a.purchase_price as "purchase_price",

               a.main_first_name as "main_first_name",
               a.main_last_name as "main_last_name",
               a.email as "email",

               {joint_columns}

               (CASE
                WHEN u.id IS NULL THEN ''
                ELSE CONCAT(u.first_name, ' ', u.last_name)
                END) as "user_full_name",
               u.username as "user_username",
               u.id as "user_id",

               (CASE
                WHEN s.id IS NULL THEN ''
                ELSE CONCAT(s.first_name, ' ', s.last_name)
                END) as "submitting_user_full_name",
               s.username as "submitting_user_username",
               s.id as "submitting_user_id",

               to_tsvector(
                   {name_vector}
               ) as "name",
               to_tsvector(
                   {address_vector}
               ) as "address",
               to_tsvector(
                   {phone_vector}
               ) as "phone",
               to_tsvector(
                   {text_vector}
               ) as "text"
          FROM {app_table_name} a
          LEFT JOIN wellsfargo_apicredentials c
            ON c.id = a.credentials_id
          LEFT JOIN {user_table_name} u
            ON u.id = a.user_id
          LEFT JOIN {user_table_name} s
            ON s.id = a.submitting_user_id
    """
    query = query_template.format(
        app_type_code=AppModel.APP_TYPE_CODE,
        joint_columns=joint_columns.strip(),
        name_vector=name_vector.strip(),
        address_vector=address_vector.strip(),
        phone_vector=phone_vector.strip(),
        text_vector=text_vector.strip(),
        app_table_name=AppModel._meta.db_table,
        user_table_name=get_user_model()._meta.db_table,
    )
    return query.strip()



CREDIT_APP_INDEX_SQL = "\nUNION\n".join([
    _build_credit_app_query(USCreditApp, False),
    _build_credit_app_query(USJointCreditApp, True),
    _build_credit_app_query(CACreditApp, False),
    _build_credit_app_query(CAJointCreditApp, True),
])


CREDIT_APP_INDEX_INDEXES = [
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_created_datetime
        ON wellsfargo_creditappindex
     USING btree(created_datetime);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_user_id
        ON wellsfargo_creditappindex
     USING btree(user_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_submitting_user_id
        ON wellsfargo_creditappindex
     USING btree(submitting_user_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_gin_name
        ON wellsfargo_creditappindex
     USING gin(name);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_gin_address
        ON wellsfargo_creditappindex
     USING gin(address);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_gin_phone
        ON wellsfargo_creditappindex
     USING gin(phone);
    """,
    """
    CREATE INDEX IF NOT EXISTS wellsfargo_creditappindex_gin_text
        ON wellsfargo_creditappindex
     USING gin(text);
    """,
]



class CreditAppIndex(pg.MaterializedView):
    app_type_code = models.CharField(max_length=15)
    id = models.AutoField(primary_key=True)

    merchant_name = models.CharField(max_length=200)
    status = models.CharField(max_length=2)
    application_source = models.CharField(max_length=25)
    modified_datetime = models.DateTimeField()
    created_datetime = models.DateTimeField()

    account_number = models.CharField(max_length=16, null=True)
    purchase_price = models.IntegerField(null=True)

    main_first_name = citext.CICharField(max_length=15)
    main_last_name = citext.CICharField(max_length=20)
    email = citext.CIEmailField()

    joint_first_name = citext.CICharField(max_length=15)
    joint_last_name = citext.CICharField(max_length=20)

    user_full_name = citext.CICharField(max_length=200)
    user_username = citext.CICharField(max_length=150, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True, related_name='+',
        on_delete=models.DO_NOTHING)

    submitting_user_full_name = citext.CICharField(max_length=200)
    submitting_user_username = citext.CICharField(max_length=150, null=True)
    submitting_user = models.ForeignKey(settings.AUTH_USER_MODEL,
        null=True, blank=True, related_name='+',
        on_delete=models.DO_NOTHING)

    name = SearchVectorField()
    address = SearchVectorField()
    phone = SearchVectorField()
    text = SearchVectorField()

    concurrent_index = 'app_type_code, id'
    sql = CREDIT_APP_INDEX_SQL

    class Meta:
        managed = False
        indexes = [
            GinIndex(fields=['name']),
            GinIndex(fields=['address']),
            GinIndex(fields=['phone']),
            GinIndex(fields=['text']),
        ]


    @property
    def APP_TYPE_CODE(self):
        return self.app_type_code


    @cached_property
    def object(self):
        models = {
            USCreditApp.APP_TYPE_CODE: USCreditApp,
            USJointCreditApp.APP_TYPE_CODE: USJointCreditApp,
            CACreditApp.APP_TYPE_CODE: CACreditApp,
            CAJointCreditApp.APP_TYPE_CODE: CAJointCreditApp,
        }
        CreditAppModel = models[self.app_type_code]
        return CreditAppModel.objects.get(pk=self.id)



@receiver(view_synced, sender=CreditAppIndex)
def add_view_indexes(sender, **kwargs):
    with connection.cursor() as cursor:
        for sql in CREDIT_APP_INDEX_INDEXES:
            cursor.execute(sql)
