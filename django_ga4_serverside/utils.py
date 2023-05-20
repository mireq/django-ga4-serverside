# -*- coding: utf-8 -*-
import contextvars
import logging
import random
import re
import typing
from dataclasses import dataclass
from importlib import import_module
from typing import Optional, Tuple, Dict

from crawlerdetect import CrawlerDetect
from django.conf import settings
from django.utils import timezone
from lxml import html


if typing.TYPE_CHECKING:
	from django.http.response import HttpResponse
	from django.http.request import HttpRequest


_context = contextvars.ContextVar('context')
logger = logging.getLogger(__name__)
ANALYTICS_EVENTS_KEY = '_analytics'
COOKIE_NAME = '_uid'
COOKIE_AGE = 31536000 # 1 year
if ignore_url_regex := getattr(settings, 'GA4_IGNORE_URL_REGEX', None):
	ignore_url_regex = re.compile(ignore_url_regex)


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


def store_context(request: 'HttpRequest', response: 'HttpResponse') -> RequestContext:
	if request is not None and not hasattr(request, ANALYTICS_EVENTS_KEY):
		setattr(request, ANALYTICS_EVENTS_KEY, {'events': []})
	ctx = RequestContext(request, response)
	_context.set(ctx)
	return ctx


def get_context() -> Optional[RequestContext]:
	return _context.get(None)


def clear_context():
	return _context.set(None)


def _get_request_payload(request: 'HttpRequest' = None):
	if request is None:
		context = get_context()
		if context is None:
			logger.error("Request not available, check if django_ga4_serverside.middleware.TrackingMiddleware is in MIDDLEWARE settings")
			return
		request = context.request
	return getattr(request, ANALYTICS_EVENTS_KEY)


def store_event(name: str, params: dict, request: 'HttpRequest' = None):
	payload = _get_request_payload(request)
	if payload is not None:
		payload['events'].append({
			'name': name,
			'params': params,
		})


def store_parameters(request: 'HttpRequest' = None, **kwargs: Dict[str, str]):
	payload = _get_request_payload(request)
	if payload is not None:
		payload.update(kwargs)


def get_payload() -> Optional[dict]:
	context = get_context()
	if context is None:
		return None
	return getattr(context.request, ANALYTICS_EVENTS_KEY)


def generate_client_id() -> str:
	rnd = random.randint(0, 4294967296)
	time = int(timezone.now().timestamp())
	return f'{rnd}.{time}'


def get_or_create_client_id(request: 'HttpRequest') -> Tuple[str, bool]:
	client_id = request.COOKIES.get(COOKIE_NAME)
	if client_id is None:
		return generate_client_id(), True
	else:
		return client_id, False


def store_user_cookie(response: 'HttpResponse', client_id: str):
	response.set_cookie(
		COOKIE_NAME,
		client_id,
		max_age=COOKIE_AGE,
	)


def _process_analytics(context: RequestContext):
	client_id, created = get_or_create_client_id(context.request)
	if created:
		store_user_cookie(context.response, client_id)
	store_parameters(context.request, client_id=client_id)


def process_analytics(context: RequestContext):
	if process_analytics.impl is None:
		return _process_analytics(context)
	else:
		return process_analytics.impl(context)
process_analytics.impl = None # overriden module


if getattr(settings, 'GA4_PROCESS_ANALYTICS', None):
	process_analytics.impl = get_absolute_name(settings.GA4_PROCESS_ANALYTICS)


def get_page_info(context: RequestContext) -> Optional[dict]:
	# cannot get info from other sources than HTML
	content_type = context.response.headers.get('Content-Type', '')
	if not content_type.startswith('text/html'):
		return

	# skip streaming and empty responses
	try:
		content = context.response.content
	except AttributeError:
		return
	if not content:
		return

	document = html.fromstring(content)
	page_title = ''
	page_title_element = document.find('./head/title')
	if page_title_element is not None:
		page_title = page_title_element.text.strip()

	return {
		'page_location': context.request.build_absolute_uri(context.request.get_full_path()),
		'page_title': page_title,
	}


def _generate_payload(context: RequestContext) -> Optional[dict]:
	# dont continue if payload is not defined
	payload = get_payload()
	if not payload:
		return

	#store only OK responses
	if context.response.status_code != 200:
		return

	# record only HTML
	content_type = context.response.headers.get('Content-Type', '')
	if not content_type.startswith('text/html'):
		return

	# generate page view event if it's needed
	has_page_view = any(event.get('name') == 'page_view' for event in payload['events'])

	if not has_page_view:
		page_info = get_page_info(context)
		if page_info is not None:
			payload['events'].insert(0, {
				'name': 'page_view',
				'params': page_info,
			})

	user_agent = context.request.headers.get('User-Agent')
	if user_agent:
		user_agent = user_agent[:100]
	referer = context.request.headers.get('Referer')

	for event in payload['events']:
		event.setdefault('params', {})
		event['params'].setdefault('engagement_time_msec', 1)

		for field, value in [('user_agent', user_agent), ('page_referrer', referer)]:
			if value:
				event['params'].setdefault(field, value)

	# don't send empty payloads
	if not payload['events']:
		return

	return payload


def generate_payload(context: RequestContext) -> Optional[dict]:
	if generate_payload.impl is None:
		return _generate_payload(context)
	else:
		return generate_payload.impl(context)
generate_payload.impl = None # overriden module


if getattr(settings, 'GA4_GENERATE_PAYLOAD', None):
	generate_payload.impl = get_absolute_name(settings.GA4_GENERATE_PAYLOAD)


crawler_detect = CrawlerDetect()


def _should_track_callback(context: RequestContext) -> bool:
	if ignore_url_regex and ignore_url_regex.match(context.request.path):
		return False
	user_agent = context.request.headers.get('User-Agent')
	if not user_agent:
		return False
	if crawler_detect.isCrawler(user_agent):
		return False
	return True


def should_track_callback(context: RequestContext) -> bool:
	if should_track_callback.impl is None:
		return _should_track_callback(context)
	else:
		return should_track_callback.impl(context)
should_track_callback.impl = None # overriden module


if getattr(settings, 'GA4_SHOULD_TRACK_CALLBACK', None):
	should_track_callback.impl = get_absolute_name(settings.GA4_SHOULD_TRACK_CALLBACK)
