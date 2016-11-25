#!/usr/bin/python
"""
Same, but for easier maintenance, use HTML template strings, 
get the Language table and input key from common module file, 
and get reusable form field mockup utilities module for testing.
"""

import cgi
import sys

from formMockup import FieldMockup
from languages2common import hellos, inputkey

debugMode = False

hdrhtml = """Content-type: text/html\n
<TITLE>Languages</TITLE>
<H1>Syntax</H1><HR>"""

langhtml = """
<H3>%s</H3><P><PRE>
%s
</PRE></P><BR>"""

def showHello(form):

    choice = form[inputkey].value

    try:
        print(langhtml % (cgi.escape(choice), cgi.escape(hellos[choice])))
    except KeyError:
        print(langhtml % (cgi.escape(choice), "Sorry--I don't know that language"))
        
def main():
    if debugMode:
        form = {inputkey: FieldMockup(sys.argv[1])}
    else:
        form = cgi.FieldStorage()
    
    print(hdrhtml)
    if not inputkey in form or form[inputkey].value == 'All':
        for lang in hellos.keys():
            mock = {inputkey: FieldMockup(lang)}
            showHello(mock)
    else:
        showHello(form)
    print('<HR>')
    
if __name__ == '__main__':
    main()
