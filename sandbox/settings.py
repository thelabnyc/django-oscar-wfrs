from django.utils.translation import gettext_lazy as _
from oscar.defaults import *  # noqa
from oscarbluelight.defaults import *  # NOQA
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
SECRET_KEY = "li0$-gnv)76g$yf7p@(cg-^_q7j6df5cx$o-gsef5hd68phj!4"
SITE_ID = 1

ROOT_URLCONF = "urls"
ALLOWED_HOSTS = ["*"]

USE_TZ = True
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = "en-us"
LANGUAGES = (
    ("en-us", _("English")),
    ("es", _("Spanish")),
)

# Configure JUnit XML output
TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
_tox_env_name = os.environ.get("TOX_ENV_NAME")
if _tox_env_name:
    TEST_OUTPUT_DIR = os.path.join(BASE_DIR, f"../junit-{_tox_env_name}/")
else:
    TEST_OUTPUT_DIR = os.path.join(BASE_DIR, "../junit/")

INSTALLED_APPS = [
    # Core Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.postgres",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.flatpages",
    # Oscar Plugins
    "wellsfargo",
    "wellsfargo.api",
    "wellsfargo.dashboard",
    "oscarbluelight",
    "oscarapicheckout",
    "oscarapi",
    # django-oscar
    "oscar.config.Shop",
    "oscar.apps.analytics.apps.AnalyticsConfig",
    "oscar.apps.checkout.apps.CheckoutConfig",
    "oscar.apps.address.apps.AddressConfig",
    "oscar.apps.shipping.apps.ShippingConfig",
    "oscar.apps.catalogue.apps.CatalogueConfig",
    "oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig",
    "oscar.apps.communication.apps.CommunicationConfig",
    "oscar.apps.partner.apps.PartnerConfig",
    "basket.apps.BasketConfig",  # oscar.apps.basket.apps.BasketConfig
    "oscar.apps.payment.apps.PaymentConfig",
    "oscarbluelight.offer.apps.OfferConfig",  # oscar.apps.offer.apps.OfferConfig
    "order.apps.OrderConfig",  # oscar.apps.order.apps.OrderConfig
    "oscar.apps.customer.apps.CustomerConfig",
    "oscar.apps.search.apps.SearchConfig",
    "oscarbluelight.voucher.apps.VoucherConfig",  # oscar.apps.voucher.apps.VoucherConfig
    "oscar.apps.wishlists.apps.WishlistsConfig",
    "oscar.apps.dashboard.apps.DashboardConfig",
    "oscar.apps.dashboard.reports.apps.ReportsDashboardConfig",
    "oscar.apps.dashboard.users.apps.UsersDashboardConfig",
    "oscar.apps.dashboard.orders.apps.OrdersDashboardConfig",
    "oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig",
    "oscarbluelight.dashboard.offers.apps.OffersDashboardConfig",  # oscar.apps.dashboard.offers.apps.OffersDashboardConfig
    "oscar.apps.dashboard.partners.apps.PartnersDashboardConfig",
    "oscar.apps.dashboard.pages.apps.PagesDashboardConfig",
    "oscar.apps.dashboard.ranges.apps.RangesDashboardConfig",
    "oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig",
    "oscarbluelight.dashboard.vouchers.apps.VouchersDashboardConfig",  # oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig
    "oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig",
    "oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig",
    # 3rd-party apps that oscar depends on
    "widget_tweaks",
    "haystack",
    "treebeard",
    "sorl.thumbnail",
    "django_tables2",
    # 3rd-party apps depend on
    "rest_framework",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s django %(name)s: %(levelname)s %(process)d %(thread)d %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "loggers": {},
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oscar.apps.basket.middleware.BasketMiddleware",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "oscar.apps.search.context_processors.search_form",
                "oscar.apps.checkout.context_processors.checkout",
                "oscar.apps.communication.notifications.context_processors.notifications",
                "oscar.core.context_processors.metadata",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "postgres",
        "PORT": 5432,
    }
}

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.simple_backend.SimpleEngine",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "wfrs-testing-sandbox",
    }
}

AUTHENTICATION_BACKENDS = (
    "oscar.apps.customer.auth_backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
)


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")

# Order Status Pipeline
# Needed by oscarapicheckout
ORDER_STATUS_PENDING = "Pending"
ORDER_STATUS_PAYMENT_DECLINED = "Payment Declined"
ORDER_STATUS_AUTHORIZED = "Authorized"

# Other statuses
ORDER_STATUS_SHIPPED = "Shipped"
ORDER_STATUS_CANCELED = "Canceled"

OSCAR_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCARAPI_INITIAL_ORDER_STATUS = ORDER_STATUS_PENDING
OSCAR_ORDER_STATUS_PIPELINE = {
    ORDER_STATUS_PENDING: (
        ORDER_STATUS_PAYMENT_DECLINED,
        ORDER_STATUS_AUTHORIZED,
        ORDER_STATUS_CANCELED,
    ),
    ORDER_STATUS_PAYMENT_DECLINED: (ORDER_STATUS_CANCELED,),
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
OSCAR_DEFAULT_CURRENCY = "USD"
OSCARAPI_BLOCK_ADMIN_API_ACCESS = False

# Disable real emails
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

OSCAR_DASHBOARD_NAVIGATION.append(  # NOQA
    {
        "label": "Wells Fargo",
        "icon": "icon-globe",
        "children": [
            # Wells Fargo Retail Services Views
            {
                "label": _("Financing Plans"),
                "url_name": "wfrs-plan-list",
            },
            {
                "label": _("Financing Plan Groups"),
                "url_name": "wfrs-benefit-list",
            },
            {
                "label": _("Credit Applications"),
                "url_name": "wfrs-application-list",
            },
            {
                "label": _("Transfers"),
                "url_name": "wfrs-transfer-list",
            },
            {
                "label": _("Pre-Qualification Requests"),
                "url_name": "wfrs-prequal-list",
            },
        ],
    }
)

# Configure payment methods
API_ENABLED_PAYMENT_METHODS = [
    {
        "method": "oscarapicheckout.methods.Cash",
        "permission": "oscarapicheckout.permissions.Public",
    },
    {
        "method": "wellsfargo.methods.WellsFargo",
        "permission": "oscarapicheckout.permissions.Public",
    },
]

# Custom benefits
BLUELIGHT_BENEFIT_CLASSES += [  # NOQA
    (
        "wellsfargo.models.FinancingPlanBenefit",
        _("Activate Wells Fargo Plan Number Group"),
    ),
]

# WFRS
WFRS_SECURITY = {
    "encryptor_kwargs": {
        "key": b"U3Nyi57e55H2weKVmEPzrGdv18b0bGt3e542rg1J1N8=",
    },
}
