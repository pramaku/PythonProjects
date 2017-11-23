#!/usr/bin/python
"""
extract file uploaded by HTTP from web browser;

users visit putfile.html to get the upload form page, which then triggers this
 script on server. This is very powerful, and very dangerous: you will usually
 want to check the filename, etc;

this may only work if file or dir is writable: a Unix 'chmod 777 uploads'
may suffice; file pathnames may arrive in client's path format: handle here;

caveat: could open output file in text mode to wite receiving platform's line
ends since file content always str from the cgi module,
but this is a temporary solution anyhow.
--the cgi module doesn't handle binary file uploads in 3.1 at all;
"""

import cgi
import os
import sys

# handle unix, win, mac clients
import posixpath
import ntpath
import macpath

# set this to True when running from command line
debugMode = True

# set to true to read the file at once
loadtextauto = False

# the directory should be writable
uploaddir = './uploads'

sys.stderr = sys.stdout
form = cgi.FieldStorage()
print("Content-type: text/html\n")

if debugMode:
    print(cgi.print_form(form))

response = """
<html><title>Putfile response page</title>
<body>
<h1>Putfile response page</h1>
%s
</body></html>"""

validResponse = response % """
<p>Your file, '%s', has been saved on the server as '%s'.
<p>An echo of the file's contents received and saved appears below.
</p><hr>
<p><pre>%s</pre>
</p><hr>
"""


def splitPath(origpath):
    for pathmodule in (posixpath, ntpath, macpath):
        basename = pathmodule.split(origpath)[1]
        if basename != origpath:
            return basename
    return origpath


# process the content and save it in file.
def saveOnServer(fileInfo):
    basename = splitPath(fileInfo.filename)
    srvrname = os.path.join(uploaddir, basename)
    srvrfile = open(srvrname, 'wb')
    if loadtextauto:
        fileText = fileInfo.value
        if isinstance(fileText, str):
            fileData = fileText.encode()
        srvrfile.write(fileData)
    else:
        numLines = 0
        fileText = ''
        while True:
            line = fileInfo.file.readline()
            if not line:
                break
            if isinstance(line, str):
                line = line.encode()
            srvrfile.write(line)
            fileText += line.decode()
            numLines += 1
        fileText = ('[Lines=%d]\n' % numLines) + fileText
    srvrfile.close()
    os.chmod(srvrname, 0o666)
    return (fileText, srvrname)


# starts here
def main():
    if 'clientfile' not in form:
        print(response % ('No file received'))
    elif not form['clientfile'].filename:
        print(response % 'Error: filename is missing')
    else:
        fileInfo = form['clientfile']
        try:
            fileText, serverName = saveOnServer(fileInfo)
        except IOError:
            errmsg = '<h2>Error</h2><p>%s<p>%s' % tuple(sys.exc_info()[:2])
            print(response % errmsg)
        else:
            print(validResponse % (cgi.escape(fileInfo.filename),
                  cgi.escape(serverName), cgi.escape(fileText)))


main()
