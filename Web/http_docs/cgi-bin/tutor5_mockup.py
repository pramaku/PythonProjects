#!/usr/bin/python
"""
same as tutor5.py, but uses the formMock to get the inputs instead from cgi
"""
from formMockup import formMockup

form = formMockup(name='Bob', shoesize='Small',
                  language=['Python', 'C++', 'HTML'], comment='ni, Ni, NI')

print('Content-type: text/html\n')

html = """
<TITLE>tutor5.py</TITLE>
<H1>Greetings</H1>
<HR>
<H4>Your name is %(name)s</H4>
<H4>You wear rather %(shoesize)s shoes</H4>
<H4>Your current job: %(job)s</H4>
<H4>You program in %(language)s</H4>
<H4>You also said:</H4>
<P>%(comment)s</P>
<HR>"""

# fill the placeholders with keynames in the below dict.
data = {}

for field in ('name', 'shoesize', 'job', 'language', 'comment'):
    if field not in form:
        data[field] = 'unknown'
    else:
        if not isinstance(form[field], list):
            data[field] = form[field].value
        else:
            values = [x.value for x in form[field]]
            data[field] = ' and '.join(values)
print(html % data)
