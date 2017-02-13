from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import i18n as i18n_urls
from django.views.static import serve
from oscar.app import application as oscar_application
from oscarapi.app import application as oscar_api
from oscarapicheckout.app import application as oscar_api_checkout
from oscar_accounts.dashboard.app import application as accounts_app
from wellsfargo.api.app import application as wfrs_api
from wellsfargo.dashboard.app import application as wfrs_app


urlpatterns = [
    url(r'^i18n/', include(i18n_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),

    # Include plugins
    url(r'^dashboard/accounts/', include(accounts_app.urls)),
    url(r'^dashboard/wfrs/', include(wfrs_app.urls)),
    url(r'^api/wfrs/', include(wfrs_api.urls)),
    url(r'^api/', include(oscar_api_checkout.urls)),
    url(r'^api/', include(oscar_api.urls)),

    # Include stock Oscar
    url(r'', include(oscar_application.urls)),
]
