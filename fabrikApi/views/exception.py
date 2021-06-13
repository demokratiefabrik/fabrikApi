import traceback
from fabrikApi.util.lib import email_notification
from pyramid.view import exception_view_config

@exception_view_config(Exception)
def failed_validation(exc, request):
    message = "%s" % (exc)
    message = (message[:75] + '..') if len(message) > 75 else message
    body = traceback.format_exc()
    email_notification(body, "DB-ERROR -CORE: %s" % message)    
    raise exc
