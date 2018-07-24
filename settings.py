import os
from os import environ
import logging
import dj_database_url
#from boto.mturk import qualification
from datetime import datetime
import otree.settings
import yaml
import augment_configs
from oTree_HFT_CDA.exp_logging import custom_filter

CHANNEL_ROUTING = 'oTree_HFT_CDA.routing.channel_routing'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False
if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
elif 'OTREE_PRODUCTION' not in os.environ:
    DEBUG = False
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
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True


# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'en'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
# INSTALLED_APPS = ['otree', 'django_extensions']
INSTALLED_APPS = ['otree']
#EXTENSION_APPS = ['otree_redwood']

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
        'participant_label_file': 'leeps_room_labels.txt',
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
    'expiration_hours': 7*24, # 7 days
    #'grant_qualification_id': 'YOUR_QUALIFICATION_ID_HERE',# to prevent retakes
    'qualification_requirements': [
        # qualification.LocaleRequirement("EqualTo", "US"),
        # qualification.PercentAssignmentsApprovedRequirement("GreaterThanOrEqualTo", 50),
        # qualification.NumberHitsApprovedRequirement("GreaterThanOrEqualTo", 5),
        # qualification.Requirement('YOUR_QUALIFICATION_ID_HERE', 'DoesNotExist')
    ]
}

# patch logging to add new level

logging.EXP = logging.DEBUG - 5     # define new log level

logging.addLevelName(logging.EXP, 'EXP')

def experiment(self, message, *args, **kws):
    """
    sends log record to custom log level
    """
    self.log(logging.EXP, message, *args, **kws) 

logging.Logger.experiment = experiment
logging.custom_filter = custom_filter

# configure logging in json style

today = datetime.now().strftime('%Y-%m-%d_%H-%M')   # get todays date

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

        'json': {
            'fmt': '%(message)s',
        }
    },

    'filters': {
        'lablog': {
            '()': 'oTree_HFT_CDA.exp_logging.custom_filter',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple'
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
            'filename': os.path.join(os.getcwd(), ('logs/' + today  + '.txt'))
        },
        'explogfile': {
            'class': 'logging.FileHandler',
            'level': 'EXP',
            'formatter': 'json',
            'filters': ['lablog'],
            'filename': os.path.join(os.getcwd(), ('logs/exp_' + today + '.txt'))
        }
    },
    'loggers': {
        'oTree_HFT_CDA': {
            'handlers': ['console', 'logfile', 'explogfile'],
            'level': 'EXP',
            'propagate': False
        }
    }
    
}


# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.00,
    'participation_fee': 0.00,
    'mturk_hit_settings': mturk_hit_settings,
    'app_sequence': ['oTree_HFT_CDA'],
    'exchange_host': '127.0.0.1',
    'speed_cost': 0.01,
    'fundamental_price': 100,
    'initial_spread': 2,
    'initial_endowment': 20,
    'session_length': 240, 
    'number_of_groups': 1,
    'players_per_group': 3,
}

SESSION_CONFIGS = [
    {
        'name': 'oTree_HFT_CDA_1',
        'display_name': 'Continous Double Auction - 3 Players 1 Group',
        'num_demo_participants': 3,
        'investors_group_1': os.path.join(os.getcwd(), 'session_config/test/investors_test.csv'),
        'jumps_group_1': os.path.join(os.getcwd(), 'session_config/test/jumps_test.csv'),
        'app_sequence': ['oTree_HFT_CDA'],
        'players_per_group': 3,
        'session_length': 240,
    },
    {
        'name': 'oTree_HFT_CDA_2',
        'display_name': 'Continous Double Auction - 3 Players 2 Groups',
        'num_demo_participants': 6,
        'investors_group_1': os.path.join(os.getcwd(), 'session_config/test/investors_test.csv'),
        'jumps_group_1': os.path.join(os.getcwd(), 'session_config/test/jump_stest.csv'),
        'investors_group_2': os.path.join(os.getcwd(), 'session_config/test/investors_test.csv'),
        'jumps_group_2': os.path.join(os.getcwd(), 'session_config/test/jumps_test.csv'),
        'app_sequence': ['oTree_HFT_CDA'],
        'players_per_group': 3,
        'session_length': 240,
    },
]

SESSION_CONFIGS = augment_configs.augment(SESSION_CONFIGS)

# anything you put after the below line will override
# oTree's default settings. Use with caution.
otree.settings.augment_settings(globals())
