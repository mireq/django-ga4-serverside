# -*- coding: utf-8 -*-
import contextvars
import logging
from collections import namedtuple
from typing import Optional, List


_last = contextvars.ContextVar('last')
logger = logging.getLogger(__name__)
ANALYTICS_EVENTS_KEY = '_analytics'
LastRequest = namedtuple('LastRequest', ['request', 'response'])


def store_last(request, response) -> contextvars.Token:
	if request is not None and not hasattr(request, ANALYTICS_EVENTS_KEY):
		setattr(request, ANALYTICS_EVENTS_KEY, [])
	return _last.set(LastRequest(request, response))


def get_last() -> Optional[LastRequest]:
	return _last.get(None)


def store_event(event: dict):
	last_request = get_last()
	if last_request is None:
		logger.error("Request not available, check if django_ga4_serverside.middleware.TrackingMiddleware is in MIDDLEWARE settings")
		return
	getattr(last_request.request, ANALYTICS_EVENTS_KEY).append(event)


def get_stored_events() -> List[dict]:
	last_request = get_last()
	if last_request is None:
		return []
	return getattr(last_request.request, ANALYTICS_EVENTS_KEY)
