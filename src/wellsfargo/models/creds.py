from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger(__name__)



class APICredentials(models.Model):
    name = models.CharField(_('Merchant Name'), max_length=200, default='Default')
    username = models.CharField(_('WFRS API Username'), max_length=200)
    password = models.CharField(_('WFRS API Password'), max_length=200)
    merchant_num = models.CharField(_('WFRS API Merchant Number'), max_length=200)
    user_group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)
    priority = models.IntegerField(_('Priority Order'), default=1)

    class Meta:
        ordering = ('-priority', '-id')
        verbose_name = _('API Credentials')
        verbose_name_plural = _('API Credentials')


    @classmethod
    def get_credentials(cls, user=None):
        if user and user.is_authenticated:
            creds = cls.objects.filter(user_group__in=user.groups.all()).first()
            if creds:
                return creds
        creds = cls.objects.filter(user_group=None).first()
        if creds:
            return creds
        logger.error('Application requested WFRS API Credentials for use by user {}, but none exist in the database for them.'.format(user))
        return cls()


    def __str__(self):
        return "%s:xxxx@wfrs/%s" % (self.username, self.merchant_num)
