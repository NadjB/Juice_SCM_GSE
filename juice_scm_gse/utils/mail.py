#!/usr/bin/env python3

__author__ = "Alexis Jeandet"
__copyright__ = "Copyright 2017, Laboratory of Plasma Physics"
__credits__ = []
__license__ = "GPLv2"
__version__ = "1.0.0"
__maintainer__ = "Alexis Jeandet"
__email__ = "alexis.jeandet@member.fsf.org"
__status__ = "Development"

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_mail(server, sender, recipients, subject, html_body, username=None, password=None, port=0, use_tls='False', **kwargs):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipients
    msg.attach(MIMEText(html_body, 'html'))
    if use_tls == 'True':
        s = smtplib.SMTP_SSL(server, port)
    else:
        s = smtplib.SMTP(server, port)
    if username is not None and password is not None:
        s.login(username, password)
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()
