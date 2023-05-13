# -*- coding: utf-8 -*-
import contextvars
import logging
from collections import namedtuple
from typing import Optional, List


_context = contextvars.ContextVar('context')
logger = logging.getLogger(__name__)
ANALYTICS_EVENTS_KEY = '_analytics'
LastRequest = namedtuple('LastRequest', ['request', 'response'])


def store_context(request, response) -> contextvars.Token:
	if request is not None and not hasattr(request, ANALYTICS_EVENTS_KEY):
		setattr(request, ANALYTICS_EVENTS_KEY, [])
	return _context.set(LastRequest(request, response))


def get_context() -> Optional[LastRequest]:
	return _context.get(None)


def store_event(event: dict):
	context = get_context()
	if context is None:
		logger.error("Request not available, check if django_ga4_serverside.middleware.TrackingMiddleware is in MIDDLEWARE settings")
		return
	getattr(context.request, ANALYTICS_EVENTS_KEY).append(event)


def get_stored_events() -> List[dict]:
	context = get_context()
	if context is None:
		return []
	return getattr(context.request, ANALYTICS_EVENTS_KEY)
