#!/usr/bin/python
"""
Implement an HTTP web server in Python which knows how to serve HTML pages and
run server-side CGI scripts coded in Python;

this is not a production-grade server (e.g., no HTTPS, slow script launch/run
on some platforms), but suffices for testing, especially on localhost;

Serves files and scripts from the current working dir and port 80 by default,
unless these options are specified in command-line arguments;

Python CGI scripts must be stored in webdir\cgi-bin or webdir\htbin;

more than one of this server may be running on the same machine to serve from
different directories, as long as they listen on different ports;
"""

import os
import sys
from http.server import HTTPServer
from http.server import CGIHTTPRequestHandler

# set this to the directory where the HTML files and CGI bin directory lives
webdir = '/home/pradeep/Python/Programs/Projects/PythonProjects/Web/http_docs'

# use test port as of now instead of standard port:80
port = 58000

if len(sys.argv) > 1:
    webdir = sys.argv[1]

if len(sys.argv) > 2:
    port = int(sys.argv[2])

print('webdir "%s", port %s' % (webdir, port))

os.chdir(webdir)
serverAddr = ('', port)
serverObj = HTTPServer(serverAddr, CGIHTTPRequestHandler)
serverObj.serve_forever()
