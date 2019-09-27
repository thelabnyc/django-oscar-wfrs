from django.utils.translation import ugettext_lazy as _
from oscar.defaults import *  # noqa
from oscarbluelight.defaults import *  # NOQA
from psycopg2cffi import compat
import os

compat.register()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
SECRET_KEY = 'li0$-gnv)76g$yf7p@(cg-^_q7j6df5cx$o-gsef5hd68phj!4'
SITE_ID = 1

ROOT_URLCONF = 'urls'
ALLOWED_HOSTS = ['*']

USE_TZ = True
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('en-us', _('English')),
    ('es', _('Spanish')),
)

INSTALLED_APPS = [
    # Core Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.postgres',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',

    # Oscar Plugins
    'wellsfargo',
    'wellsfargo.api',
    'wellsfargo.dashboard',
    'oscarbluelight',
    'oscarapicheckout',
    'oscarapi',

    # django-oscar
    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.checkout',
    'oscar.apps.address',
    'oscar.apps.shipping',
    'oscar.apps.catalogue',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.partner',
    'basket',  # 'oscar.apps.basket',
    'oscar.apps.payment',
    'oscarbluelight.offer',  # 'oscar.apps.offer',
    'order',  # 'oscar.apps.order',
    'oscar.apps.customer',
    'oscar.apps.search',
    'oscarbluelight.voucher',  # 'oscar.apps.voucher',
    'oscar.apps.wishlists',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.users',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.catalogue',
    'oscarbluelight.dashboard.offers',  # 'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.pages',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.reviews',
    'oscarbluelight.dashboard.vouchers',  # 'oscar.apps.dashboard.vouchers',
    'oscar.apps.dashboard.communications',
    'oscar.apps.dashboard.shipping',

    # 3rd-party apps that oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',

    # 3rd-party apps depend on
    'rest_framework',
    'django_pgviews',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s django %(name)s: %(levelname)s %(process)d %(thread)d %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    }
}

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.apps.customer.notifications.context_processors.notifications',
                'oscar.core.context_processors.metadata',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'postgres',
        'PORT': 5432,
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'wfrs-testing-sandbox',
    }
}

AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')

# Order Status Pipeline
# Needed by oscarapicheckout
ORDER_STATUS_PENDING = 'Pending'
ORDER_STATUS_PAYMENT_DECLINED = 'Payment Declined'
ORDER_STATUS_AUTHORIZED = 'Authorized'

# Other statuses
ORDER_STATUS_SHIPPED = 'Shipped'
ORDER_STATUS_CANCELED = 'Canceled'

OSCAR_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCARAPI_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCAR_ORDER_STATUS_PIPELINE = {
    ORDER_STATUS_PENDING: (ORDER_STATUS_PAYMENT_DECLINED, ORDER_STATUS_AUTHORIZED, ORDER_STATUS_CANCELED),
    ORDER_STATUS_PAYMENT_DECLINED: (ORDER_STATUS_CANCELED, ),
    ORDER_STATUS_AUTHORIZED: (ORDER_STATUS_SHIPPED, ORDER_STATUS_CANCELED),
    ORDER_STATUS_SHIPPED: (),
    ORDER_STATUS_CANCELED: (),
}

OSCAR_INITIAL_LINE_STATUS = ORDER_STATUS_PENDING
OSCAR_LINE_STATUS_PIPELINE = {
    ORDER_STATUS_PENDING: (ORDER_STATUS_SHIPPED, ORDER_STATUS_CANCELED),
    ORDER_STATUS_SHIPPED: (),
    ORDER_STATUS_CANCELED: (),
}

# Oscar
OSCAR_SHOP_NAME = _("WFRS Sandbox")
OSCAR_ALLOW_ANON_CHECKOUT = True
OSCAR_DEFAULT_CURRENCY = 'USD'
OSCARAPI_BLOCK_ADMIN_API_ACCESS = False

# Disable real emails
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

OSCAR_DASHBOARD_NAVIGATION.append({  # NOQA
    'label': 'Wells Fargo',
    'icon': 'icon-globe',
    'children': [
        # Wells Fargo Retail Services Views
        {
            'label': _('Apply for a Credit Line (Wells Fargo)'),
            'url_name': 'wfrs-apply-step1',
        },
        {
            'label': _('Financing Plans'),
            'url_name': 'wfrs-plan-list',
        },
        {
            'label': _('Financing Plan Groups'),
            'url_name': 'wfrs-benefit-list',
        },
        {
            'label': _('Credit Applications'),
            'url_name': 'wfrs-application-list',
        },
        {
            'label': _('Transfers'),
            'url_name': 'wfrs-transfer-list',
        },
        {
            'label': _('Pre-Qualification Requests'),
            'url_name': 'wfrs-prequal-list',
        },
    ]
})

# Configure payment methods
API_ENABLED_PAYMENT_METHODS = [
    {
        'method': 'oscarapicheckout.methods.Cash',
        'permission': 'oscarapicheckout.permissions.Public',
    },
    {
        'method': 'wellsfargo.methods.WellsFargo',
        'permission': 'oscarapicheckout.permissions.Public',
    },
]

# Custom benefits
BLUELIGHT_BENEFIT_CLASSES += [  # NOQA
    ('wellsfargo.models.FinancingPlanBenefit', _('Activate Wells Fargo Plan Number Group')),
]

# WFRS
WFRS_SECURITY = {
    'encryptor_kwargs': {
        'key': b'U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8=',
    },
}
