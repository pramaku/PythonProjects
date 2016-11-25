#!/usr/bin/python
"""
Display any CGI (or other) server-side file without running it.
The filename can be passed in a URL param or form field.

http://servername/cgi-bin/getfile.py?filename=somefile.html
http://servername/cgi-bin/getfile.py?filename=cgi-bin\somefile.py
http://servername/cgi-bin/getfile.py?filename=cgi-bin%2Fsomefile.py

Users can cut-and-paste or "View Source" on the browser to save file locally.

We also check the filename here to try to avoid showing private files; 
this may or may not prevent access to such files in general: 
don't install this script if you can't otherwise secure source!
"""

import cgi
import os
import sys

#set this to false to send file contents in plain text
formatText = False

#add files here to restrcit access/transfer
privateFiles = ['cgi-bin/cookies.py']

try:
    samefile = os.path.samefile
except:
    #samefile method not avaialble on windows
    def samefile(path1, path2):
        absPath1 = os.path.abspath(path1).lower()
        absPath2 = os.path.abspath(path2).lower()
        return absPath1 == absPath2

#html content
html = """
<html><title>Getfile response</title>
<h1>Source code for: '%s'</h1>
<hr>
<pre>%s</pre>
<hr></html>"""

def restricted(filename):
    for path in privateFiles:
        if samefile(filename, path):
            return True

#get filename from request
try:
    form = cgi.FieldStorage()
    filename = form['filename'].value
except:
    filename = 'cgi-bin/getfile.py'

#load the file contents
try:
    assert not restricted(filename)
    filetext = open(filename).read()
except AssertionError:
    filetext='(File Access denied: %s)' % filename
except:
    filetext='(Error opening file: %s)' % sys.exc_info()[1]
    
if not formatText:
    print('Content-type: text/plain\n')
    print(filetext)
else:
    print('Content-type: text/html\n')
    print(html % (filename, cgi.escape(filetext)))
