#!/usr/bin/python
"""
runs on the server, reads form input, prints HTML;
URL http://server-name/cgi-bin/tutor4.py
"""

import cgi
import sys

# divert errors to browser
sys.stderr = sys.stdout

form = cgi.FieldStorage()

print('Content-type: text/html\n')

# uncomment the below code for testing from command line
# class dummy:
#    def __init__(self, s):
#        self.value = s
# form = {'user': dummy('bob'), 'age':dummy('10')}

html = """
<TITLE>tutor4.py</TITLE>
<H1>Greetings</H1>
<HR>
<H4>%s</H4>
<H4>%s</H4>
<H4>%s</H4>
<HR>"""

if 'user' not in form:
    line1 = 'Who are you?'
else:
    line1 = 'Hello, %s.' % form['user'].value

line2 = "You're talking to a %s server." % sys.platform

line3 = ""
if 'age' in form:
    try:
        line3 = "Your age squared is %d!" % (int(form['age'].value) ** 2)
    except KeyError:
        line3 = "Sorry, I can't compute %s ** 2." % form['age'].value

# append the placeholders, send to browser
print(html % (line1, line2, line3))
