#!/usr/bin/python

"""
create or use a client-side cookie storing username;
there is no input form data to parse in this example
"""

import http.cookies
import os

cookstr = os.environ.get('HTTP_COOKIE')
cookies = http.cookies.SimpleCookie(cookstr)

user = cookies.get('user')

#create if no cookie
if user == None:
    cookies = http.cookies.SimpleCookie(cookstr)
    cookies['user'] = 'Brian'
    
    #printing to stdout, this will set the cookie
    print(cookies)
    
    greeting = '<p>His name shall be... %s</p>' % cookies['user'].value
else:
    greeting = '<p>Welcome back, %s</p>' % user.value

print('Content-type: text/html\n')
print(greeting)

"""
To test cookies from urllib module:
from urllib.request import urlopen
import urllib.request as urllib
opener = urllib.build_opener(urllib.HTTPCookieProcessor())
urllib.install_opener(opener)

>>> reply = urlopen('http://localhost:58000/cgi-bin/cookies.py').read()
>>> reply
b'<p>His name shall be... Brian</p>\n'
>>> reply = urlopen('http://localhost:58000/cgi-bin/cookies.py').read()
>>> reply
b'<p>Welcome back, Brian</p>\n'
"""
