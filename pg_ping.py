# -*- coding: utf-8 -*-
import psycopg2
import sys

from django.db import connections

try:
	connection = psycopg2.connect(
	    database=connections['default'].settings_dict['NAME'],
	    user=connections['default'].settings_dict['USER'],
	    password=connections['default'].settings_dict['PASSWORD'],
	    host=connections['default'].settings_dict['HOST'],
	    port=connections['default'].settings_dict['PORT']
	)
except psycopg2.OperationalError as e:
	sys.exit("The database is not ready.")
