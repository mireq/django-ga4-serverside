# -*- coding: utf-8 -*-
import contextvars
import logging
import random
import typing
from dataclasses import dataclass
from importlib import import_module
from typing import Optional, List, Tuple

from django.conf import settings
from django.utils import timezone


if typing.TYPE_CHECKING:
	from django.http.response import HttpResponse
	from django.http.request import HttpRequest


_context = contextvars.ContextVar('context')
logger = logging.getLogger(__name__)
ANALYTICS_EVENTS_KEY = '_analytics'
COOKIE_NAME = '_uid'
COOKIE_AGE = 31536000 # 1 year


@dataclass
class RequestContext:
	request: 'HttpRequest'
	response: 'HttpResponse'



def get_absolute_name(path):
	module_name, class_name = path.rsplit('.', 1)
	module = import_module(module_name)
	try:
		cls = getattr(module, class_name)
	except AttributeError:
		raise ImportError("cannot import name '%s'" % path)
	return cls


def store_context(request: 'HttpRequest', response: 'HttpResponse') -> contextvars.Token:
	if request is not None and not hasattr(request, ANALYTICS_EVENTS_KEY):
		setattr(request, ANALYTICS_EVENTS_KEY, {'events': []})
	return _context.set(RequestContext(request, response))


def get_context() -> Optional[RequestContext]:
	return _context.get(None)


def store_event(event: dict, request: 'HttpRequest' = None):
	if request is None:
		context = get_context()
		if context is None:
			logger.error("Request not available, check if django_ga4_serverside.middleware.TrackingMiddleware is in MIDDLEWARE settings")
			return
		request = context.request
	getattr(request, ANALYTICS_EVENTS_KEY)['events'].append(event)


def get_payload() -> Optional[dict]:
	context = get_context()
	if context is None:
		return None
	return getattr(context.request, ANALYTICS_EVENTS_KEY)


def generate_user_id() -> str:
	rnd = random.randint(0, 4294967296)
	time = int(timezone.now().timestamp())
	return f'{rnd}.{time}'


def get_or_create_user_id(request: 'HttpRequest') -> Tuple[str, bool]:
	user_id = request.COOKIES.get(COOKIE_NAME)
	if user_id is None:
		return generate_user_id(), True
	else:
		return user_id, False


def store_user_cookie(response: 'HttpResponse', user_id: str):
	response.set_cookie(
		COOKIE_NAME,
		user_id,
		max_age=COOKIE_AGE,
	)


def _process_analytics(request: 'HttpRequest', response: 'HttpResponse'):
	user_id, created = get_or_create_user_id(request)
	if created:
		store_user_cookie(response, user_id)


def process_analytics(request, response: 'HttpResponse'):
	if process_analytics.impl is None:
		return _process_analytics(request, response)
	else:
		process_analytics.impl(request, response)
process_analytics.impl = None # overriden module


if getattr(settings, 'GA4_PROCESS_ANALYTICS', None):
	process_analytics.impl = get_absolute_name(settings.GA4_PROCESS_ANALYTICS)
