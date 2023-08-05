import os
from os import environ
import logging
import dj_database_url
#from boto.mturk import qualification
from datetime import datetime
#import otree.settings # comentado por cambio de version de otree
import yaml
from custom_otree_config import CustomOtreeConfig
import sys

# modificaciones asociadas a django
from django.conf import settings

CHANNEL_ROUTING = 'hft.routing.channel_routing'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POINTS_DECIMAL_PLACES = 2

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False

if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
# elif 'OTREE_PRODUCTION' not in os.environ:
#     DEBUG = False
else:
    DEBUG = True

INTERNAL_IPS = (
    '0.0.0.0',
    '127.0.0.1',
)

# don't share this with anybody.
# SECRET_KEY = '{{ secret_key }}'
ADMIN_USERNAME = 'admin'

# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

# don't share this with anybody.
SECRET_KEY = '7n786ty33t%4n-91z!*(n^y928_@4%o-vbw@ads29^-*t+2txj'

DATABASES = {
    'default': dj_database_url.config(
        # Rather than hardcoding the DB parameters here,
        # it's recommended to set the DATABASE_URL environment variable.
        # This will allow you to use SQLite locally, and postgres/mysql
        # on the server
        # Examples:
        # export DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/NAME
        # export DATABASE_URL=mysql://USER:PASSWORD@HOST:PORT/NAME

        # fall back to SQLite if the DATABASE_URL env var is missing
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

redis_at = os.environ.get('REDIS_URL', "redis://127.0.0.1:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_at,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
    }
}

# AUTH_LEVEL:
# this setting controls which parts of your site are freely accessible,
# and which are password protected:
# - If it's not set (the default), then the whole site is freely accessible.
# - If you are launching a study and want visitors to only be able to
#   play your app if you provided them with a start link, set it to STUDY.
# - If you would like to put your site online in public demo mode where
#   anybody can play a demo version of your game, but not access the rest
#   of the admin interface, set it to DEMO.

# for flexibility, you can set it in the environment variable OTREE_AUTH_LEVEL
AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')


# setting for integration with AWS Mturk
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')


# e.g. EUR, CAD, GBP, CHF, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False
POINTS_CUSTOM_NAME = 'ECUs'

# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'en'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
# INSTALLED_APPS = ['otree', 'django_extensions']
INSTALLED_APPS = ['hft','otree', 'huey.contrib.djhuey']
EXTENSION_APPS = ['Consent', 'AnonPay'] 

# SENTRY_DSN = ''

DEMO_PAGE_INTRO_TEXT = """
<ul>
    <li>
        <a href="https://github.com/oTree-org/otree" target="_blank">
            oTree on GitHub
        </a>.
    </li>
    <li>
        <a href="http://www.otree.org/" target="_blank">
            oTree homepage
        </a>.
    </li>
</ul>
<p>
    Here are various games implemented with oTree. These games are all open
    source, and you can modify them as you wish.
</p>
"""

ROOMS = [
    {
        'name': 'leeps',
        'display_name': 'LEEPS Lab',
        'participant_label_file': 'leeps_room_labels.txt'
    },
    {
        'name': 'cologne',
        'display_name': 'COLOGNE Lab',
        'participant_label_file': 'cologne_room_labels.txt',
    }
]


# from here on are qualifications requirements for workers
# see description for requirements on Amazon Mechanical Turk website:
# http://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html
# and also in docs for boto:
# https://boto.readthedocs.org/en/latest/ref/mturk.html?highlight=mturk#module-boto.mturk.qualification

mturk_hit_settings = {
    'keywords': ['easy', 'bonus', 'choice', 'study'],
    'title': 'Title for your experiment',
    'description': 'Description for your experiment',
    'frame_height': 500,
    'preview_template': 'global/MTurkPreview.html',
    'minutes_allotted_per_assignment': 60,
    'expiration_hours': 7*24,  # 7 days
    # 'grant_qualification_id': 'YOUR_QUALIFICATION_ID_HERE',# to prevent retakes
    'qualification_requirements': [
        # qualification.LocaleRequirement("EqualTo", "US"),
        # qualification.PercentAssignmentsApprovedRequirement("GreaterThanOrEqualTo", 50),
        # qualification.NumberHitsApprovedRequirement("GreaterThanOrEqualTo", 5),
        # qualification.Requirement('YOUR_QUALIFICATION_ID_HERE', 'DoesNotExist')
    ]
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s|%(asctime)s] [%(filename)s:%(lineno)s - %(funcName)20s()] %(message)s'
        },

        'simple': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },

    },
    'loggers': {
        'django.channels': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'hft': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}


matching_engine_hosts = {i: environ.get(
    '_'.join(
        (i, 'HOST')
    )) for i in ('CDA', 'FBA', 'IEX')
}
# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 1,
    'participation_fee': 0.00,
    'mturk_hit_settings': mturk_hit_settings,
    'session_length': 240,
    'doc': '',
    'app_sequence': ['Consent', 'hft', 'AnonPay']
}
"""
    
    
    
    
}
"""

exogenous_event_configs_directory = os.path.join(
    os.getcwd(), 'session_config/exogenous_events')
test_inputs_dir = './hft/static/hft/test_input_files/{}'

# settings.py

SESSION_CONFIGS = []



# read configurations
custom_configs_directory = os.path.join(
    os.getcwd(), 'session_config/session_configs')
custom_configs = CustomOtreeConfig.initialize_many_from_folder(
    custom_configs_directory)
otree_configs = []
for config in custom_configs:
    try:
        otree_config = config.get_otree_config()
    except Exception as e:
        sys.stdout.write('failed to read configuration %s: %s' % (config, e))
    else:
        otree_configs.append(otree_config)

SESSION_CONFIGS.extend(otree_configs)
# settings.augment_settings(globals()) # comentado por cambio de version de otree
