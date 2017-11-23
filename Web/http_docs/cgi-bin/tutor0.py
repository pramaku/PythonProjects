#!/usr/bin/python
"""
runs on the server, prints HTML to create a new page;
Use: http://localhost:<port_num>/cgi-bin/tutor0.py from browser;
"""
# new line to differ from header and content
print('Content-type: text/html\n')
print('<TITLE>CGI 101</TITLE>')
print('<H1>A First CGI Script</H1>')
print('<P>Hello, CGI World!</P>')
