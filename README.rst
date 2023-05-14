========================
Server side GA4 tracking
========================

Install
-------

`pip install django-ga4-serverside`


Settings
--------

.. code:: python

	INSTALLED_APPS = [
		# …
		'django_ga4_serverside',
	]

	MIDDLEWARE = [
		# …
		'django_ga4_serverside.middleware.TrackingMiddleware',
	]

	GA4_ID = 'G-XXXXXXXXXX'
	GA4_SECRET = 'XXXXXXXXXX-XXXXXXXXXXX'
	GA4_DEBUG = False

Advanced settings
^^^^^^^^^^^^^^^^^

`GA4_IGNORE_URL_REGEX` - allows to configure ignored URLs

`GA4_PROCESS_ANALYTICS` - callback used to modify payload. Default
implementation configures client_id from cookies. Default implementation:


.. code:: python

	def process_analytics(context):
		client_id, created = get_or_create_client_id(context.request)
		if created:
			store_user_cookie(context.response, client_id)
		store_parameters(context.request, client_id=client_id)

`GA4_GENERATE_PAYLOAD` - callback to generate payload

`GA4_SHOULD_TRACK_CALLBACK` - callback to filter tracked requests

API
---

Storing custom events
^^^^^^^^^^^^^^^^^^^^^

.. code:: python

	from django_ga4_serverside.utils import store_event

	# inside view

	store_event('custom_event', {'custom': 'property'})
