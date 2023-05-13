# -*- coding: utf-8 -*-
from collections import namedtuple
from contextvars import ContextVar
from typing import Optional


_last = ContextVar('last')


LastRequest = namedtuple('LastRequest', ['request', 'response'])


def store_last(request, response):
	_last.set(LastRequest(request, response))


def get_last() -> Optional[LastRequest]:
	return _last.get(None)
