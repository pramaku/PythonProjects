#!/usr/bin/python
"""
use the Python SMTP mail interface module to send email messages;
this is just a simple one-shot send script--see pymail, PyMailGUI, and
PyMailCGI for clients with more user interaction features;
also see popmail.py for a script that retrieves mail, and the mailtools pkg
for attachments and formatting with the standard library email package;
"""

import smtplib
import sys
import email.utils
import mailconfig

mailserver = mailconfig.smtpservername
username = mailconfig.popusername

From = input('From?').strip()
To = input('To?').strip()
Tos = To.split(';')                             # incase multiple receipt's
Subj = input('Subject?')
Date = email.utils.formatdate()

text = ('From: %s\nTo: %s\nDate: %s\nSubject: %s\n\n' % (From, To, Date, Subj))

print('Type message text, end with line=[Ctrl+d (Unix), Ctrl+z (Windows)]')

while True:
    line = sys.stdin.readline()
    if not line:
        break
    text += line

print('Connecting...')
server = smtplib.SMTP_SSL(mailserver)                # connect, no log-in step
server.login(username, input('Password for %s:' % username))
failed = server.sendmail(From, Tos, text)
server.quit()

if failed:                                       # smtplib may raise exceptions
    print('Failed recipients:', failed)          # too, but let them pass here
else:
    print('No errors.')
print('Bye.')
