#!/usr/bin/python
"""
runs on the server, reads form input, prints HTML;
url=http://server-name/cgi-bin/tutor3.py
"""

import cgi
inputs = cgi.FieldStorage()       # Get the form inputs

print('Content-type: text/html')  # print gives the required blank line

html = """
<TITLE>tutor3.py</TITLE>
<H1>Greetings</H1>
<HR>
<P>%s</P>
<HR>"""

# 'user' is field name ( refer to tutor3.html )
if 'user' not in inputs:           # for empty input
    print(html % 'Who are you?')
else:
    print(html % ('Hello, %s' % inputs['user'].value))
