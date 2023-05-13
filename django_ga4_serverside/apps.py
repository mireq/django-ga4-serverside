# -*- coding: utf-8 -*-
from django.apps import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
	name = 'django_ga4_serverside'
	verbose_name = "GA4 server side tracking"

	def ready(self):
		from .signals import handlers # pylint: disable=unused-import
