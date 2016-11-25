#!/usr/bin/python
"""
Display languages.py script code without running it.
"""
import cgi
fileName = 'cgi-bin/languages.py'

print('Content-type: text/html\n')

print('<TITLE>Languages</TITLE>')
print("<H1>Source code: '%s'</H1>" % fileName)
print('<HR><PRE>')
print(cgi.escape(open(fileName).read()))

print('</PRE><HR>')
