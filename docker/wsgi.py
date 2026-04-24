"""WSGI entry point for production gunicorn.

Wraps the Frappe WSGI application with static file middleware,
which is normally only added by `bench serve` (dev server).
"""

import os

from frappe.app import application, application_with_statics

# Ensure static file serving is enabled for gunicorn
# (bench serve does this internally, but gunicorn skips it)
if not os.environ.get("NO_STATICS"):
    application = application_with_statics()
