# -*- coding: utf-8 -*-
from django.core.signals import request_finished
from django.dispatch.dispatcher import receiver

from ..utils import get_last


@receiver(request_finished)
def on_request_finished(sender, **kwargs): #! pylint: disable=unused-argument
	last_request = get_last()
	if last_request is None:
		return
