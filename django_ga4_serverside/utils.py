# -*- coding: utf-8 -*-
import contextvars
import logging
from collections import namedtuple
from importlib import import_module
from typing import Optional, List

from django.conf import settings


_context = contextvars.ContextVar('context')
logger = logging.getLogger(__name__)
ANALYTICS_EVENTS_KEY = '_analytics'
LastRequest = namedtuple('LastRequest', ['request', 'response'])


def get_absolute_name(path):
	module_name, class_name = path.rsplit('.', 1)
	module = import_module(module_name)
	try:
		cls = getattr(module, class_name)
	except AttributeError:
		raise ImportError("cannot import name '%s'" % path)
	return cls


def store_context(request, response) -> contextvars.Token:
	if request is not None and not hasattr(request, ANALYTICS_EVENTS_KEY):
		setattr(request, ANALYTICS_EVENTS_KEY, [])
	return _context.set(LastRequest(request, response))


def get_context() -> Optional[LastRequest]:
	return _context.get(None)


def store_event(event: dict, request = None):
	if request is None:
		context = get_context()
		if context is None:
			logger.error("Request not available, check if django_ga4_serverside.middleware.TrackingMiddleware is in MIDDLEWARE settings")
			return
		request = context.request
	getattr(request, ANALYTICS_EVENTS_KEY).append(event)


def get_stored_events() -> List[dict]:
	context = get_context()
	if context is None:
		return []
	return getattr(context.request, ANALYTICS_EVENTS_KEY)


def _process_analytics(request, response):
	print("process")


def process_analytics(request, response):
	if process_analytics.impl is None:
		return _process_analytics(request, response)
	else:
		process_analytics.impl(request, response)
process_analytics.impl = None # overriden module


if getattr(settings, 'GA4_PROCESS_ANALYTICS', None):
	process_analytics.impl = get_absolute_name(settings.GA4_PROCESS_ANALYTICS)
