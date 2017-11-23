#!/usr/bin/python
"""
Generate the content og getfile.html and include a drowp down with list of
files currently lists only files in cgi-bin directory

TODO:enhance to browse the server file system to choose file.
"""
import os

REPLY = """Content-type: text/html

<html>
    <title>Getfile: download page</title>
    <body>
        <form method=get action="getfile.py">
            <h1>Select the file from the list</h1>
            <P><select name=filename>
            %s
            </select>
            <P>
            <p><input type=submit value=Download>
        </form>
    <hr><a href="getfile.py?filename=cgi-bin/getfile_page.py">View script code
        </a>
    </body>
</html>
"""

files = os.listdir('cgi-bin')
options = []
for file in files:
    if file not in ('.', '..', '__pycache__'):
        options.append('<option>' + 'cgi-bin/' + file)
options = '\t' + '\n\t'.join(options)

print(REPLY % options)
