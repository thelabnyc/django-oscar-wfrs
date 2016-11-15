from oscar.defaults import *  # noqa
from oscarbluelight.defaults import *  # NOQA
from oscar import OSCAR_MAIN_TEMPLATE_DIR, get_core_apps
from oscarbluelight import BLUELIGHT_TEMPLATE_DIR
from oscar_accounts import TEMPLATE_DIR as ACCOUNTS_TEMPLATE_DIR
from wellsfargo import WFRS_TEMPLATE_DIR
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
SECRET_KEY = 'li0$-gnv)76g$yf7p@(cg-^_q7j6df5cx$o-gsef5hd68phj!4'
SITE_ID = 1

ROOT_URLCONF = 'urls'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.postgres',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    'widget_tweaks',
    'oscar_accounts',
    'rest_framework',
    'oscarapi',
    'oscarapicheckout',
    'wellsfargo',
] + get_core_apps([
    'oscarbluelight.dashboard.offers',
    'oscarbluelight.dashboard.vouchers',
    'oscarbluelight.offer',
    'oscarbluelight.voucher',
])


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


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            WFRS_TEMPLATE_DIR,
            ACCOUNTS_TEMPLATE_DIR,
            BLUELIGHT_TEMPLATE_DIR,
            OSCAR_MAIN_TEMPLATE_DIR,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.promotions.context_processors.promotions',
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
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://elasticsearch:9200/',
        'INDEX_NAME': 'haystack',
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
OSCAR_SHOP_NAME = "WFRS Sandbox"
OSCAR_ALLOW_ANON_CHECKOUT = True
OSCAR_DEFAULT_CURRENCY = 'USD'


# Disable real emails
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


# Appends accounts to the dashboard navigation
OSCAR_DASHBOARD_NAVIGATION.append({
    'label': 'Accounts',
    'icon': 'icon-globe',
    'children': [
        {
            'label': 'Accounts',
            'url_name': 'accounts-list',
        },
        {
            'label': 'Transfers',
            'url_name': 'transfers-list',
        },
        {
            'label': 'Deferred income report',
            'url_name': 'report-deferred-income',
        },
        {
            'label': 'Profit/loss report',
            'url_name': 'report-profit-loss',
        },
    ]
})


OSCAR_DASHBOARD_NAVIGATION.append({
    'label': 'Wells Fargo',
    'icon': 'icon-globe',
    'children': [
        # Wells Fargo Retail Services Views
        {
            'label': 'Apply for a Credit Line (Wells Fargo)',
            'url_name': 'wfrs-apply-step1',
        },
        {
            'label': 'Add existing Wells Fargo account',
            'url_name': 'wfrs-add-account',
        },
        {
            'label': 'Financing Plans',
            'url_name': 'wfrs-plan-list',
        },
        {
            'label': 'Financing Plan Groups',
            'url_name': 'wfrs-benefit-list',
        },
        {
            'label': 'Credit Applications',
            'url_name': 'wfrs-application-list',
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
        'permission': 'wellsfargo.permissions.IsAuthenticated',
    },
]

# Custom benefits
BLUELIGHT_BENEFIT_CLASSES += [  # NOQA
    ('wellsfargo.models.FinancingPlanBenefit', 'Activate Wells Fargo Plan Number Group'),
]
