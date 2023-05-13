# -*- coding: utf-8 -*-
from .utils import store_context


class TrackingMiddleware(object):
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		token = store_context(request, None) # response not available
		response = self.get_response(request)
		store_context(request, response) # response finished, store it
		return response
