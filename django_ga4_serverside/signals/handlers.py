# -*- coding: utf-8 -*-
from django.core.signals import request_finished
from django.dispatch.dispatcher import receiver

from ..utils import get_context, get_stored_events


@receiver(request_finished)
def on_request_finished(sender, **kwargs): #! pylint: disable=unused-argument
	context = get_context()
	if context is None:
		return
