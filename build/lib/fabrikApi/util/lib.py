import logging
import arrow
import smtplib
from get_docker_secret import get_docker_secret

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
# Helper Functions

def number_of_days_passed(datetime_):
    """ 
    returns the number of days passed, while considering a day to start and
    end at 03:00 UTC (in the morning)
    """
    daydiff = arrow.utcnow().shift(hours=-3).date() - datetime_.shift(hours=-3).date()
    return (daydiff.days)


def date_with_midnightlag():
    """ 
    returns todays date, while considering a day to start and
    end at 03:00 UTC (in the morning)
    """
    # TODO: localtimezone adaption
    return arrow.utcnow().shift(hours=-3)
    


def email_notification(text, h1="Meldung aus der Demokratiefabrik", level="Error"):
    """ TODO: use pyramid mailer once.... """

    EMAIL_HOST = get_docker_secret('email_host')
    HELPDESK_EMAIL = get_docker_secret('email_helpdesk')
    EMAIL_HOST_USER = get_docker_secret('email_from')
    EMAIL_PORT = get_docker_secret('email_port', 25)
    # EMAIL_USE_TLS = True if get_docker_secret('email_use_tls', 'false') == 'true' else False
    # EMAIL_USE_SSL = True if get_docker_secret('email_use_ssl', 'false') == 'true' else False
    SERVER_DB_NAME = get_docker_secret('fabrikapi_db_host')

    if SERVER_DB_NAME == 'veldev':
        return None

    subject = "Demoratiefabrik-%s: %s" % (level, SERVER_DB_NAME)
    message = 'From: {}\nTo: {}\nSubject: {}\n\n{}\n\n{}'.format(EMAIL_HOST_USER, HELPDESK_EMAIL, subject, h1, text)

    with smtplib.SMTP (host=EMAIL_HOST, port=EMAIL_PORT) as smtpObj:
        smtpObj.sendmail(EMAIL_HOST_USER, HELPDESK_EMAIL, message, mail_options=[], rcpt_options =[])

    # except smtplib.SMTPException :
    #     print(" Error : unable to send email .")
