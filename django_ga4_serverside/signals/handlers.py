# -*- coding: utf-8 -*-
import json
import logging
from urllib import request
from urllib.parse import urlencode

from django.conf import settings
from django.core.signals import request_finished
from django.dispatch.dispatcher import receiver

from ..utils import get_context, generate_payload, clear_context


MEASUREMENT_URL = 'https://www.google-analytics.com/mp/collect?'
logger = logging.getLogger(__name__)


@receiver(request_finished)
def on_request_finished(sender, **kwargs): #! pylint: disable=unused-argument
	context = get_context()
	payload = None
	if context is None:
		clear_context()
		return
	else:
		payload = generate_payload(context)
		clear_context()
		if payload is None:
			return

	query = urlencode({'measurement_id': settings.GA4_ID, 'api_secret': settings.GA4_SECRET})
	url = f'{MEASUREMENT_URL}?{query}'
	payload = json.dumps(payload).encode('utf-8')

	user_agent = context.request.headers.get('User-Agent')

	req = request.Request(url)
	req.add_header('Content-Type', 'application/json; charset=utf-8')
	if user_agent is not None:
		req.add_header('User-Agent', user_agent)
	result = request.urlopen(req, payload)
	if result.status < 200 or result.status >= 300:
		logger.warning("Failed to send event: %s", str(result.status))
