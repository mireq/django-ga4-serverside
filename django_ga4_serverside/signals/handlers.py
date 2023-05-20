# -*- coding: utf-8 -*-
import json
import logging
import sys
from urllib import request
from urllib.parse import urlencode

from django.conf import settings
from django.core.signals import request_finished
from django.dispatch.dispatcher import receiver

from ..utils import get_context, generate_payload, clear_context, should_track_callback


MEASUREMENT_URL = 'https://www.google-analytics.com/mp/collect?'
MEASUREMENT_DEBUG_URL = 'https://www.google-analytics.com/debug/mp/collect?'
logger = logging.getLogger(__name__)


@receiver(request_finished)
def on_request_finished(sender, **kwargs): #! pylint: disable=unused-argument
	context = get_context()
	payload = None
	try:
		if not context:
			return
		if not should_track_callback(context):
			return
		payload = generate_payload(context)
		if not payload:
			return
	finally:
		clear_context()

	debug = getattr(settings, 'GA4_DEBUG', False)
	query = urlencode({'measurement_id': settings.GA4_ID, 'api_secret': settings.GA4_SECRET})
	url = MEASUREMENT_DEBUG_URL if debug else MEASUREMENT_URL
	url = f'{url}{query}'
	if debug:
		sys.stdout.write(f"URL {url}\n")
		sys.stdout.write(json.dumps(payload, indent=2) + '\n')

	payload = json.dumps(payload).encode('utf-8')

	req = request.Request(url)
	req.add_header('Content-Type', 'application/json; charset=utf-8')
	req.add_header('User-Agent', 'django_ga4_serverside')
	result = request.urlopen(req, payload)
	if result.status < 200 or result.status >= 300:
		logger.warning("Failed to send event: %s", str(result.status))
	if debug:
		sys.stdout.write(json.dumps(json.loads(result.read()), indent=2) + '\n')
