#!/usr/bin/python
"""
Tools for simulating the result of a cgi.FieldStorage() call;
useful for testing CGI scripts outside the Web
"""


class FieldMockup:
    def __init__(self, str):
        self.value = str


def formMockup(**kwargs):
    mockup = {}
    for (key, value) in kwargs.items():
        if type(value) != list:
            mockup[key] = FieldMockup(str(value))
        else:
            mockup[key] = []
            for pick in value:
                mockup[key].append(FieldMockup(str(pick)))

    return mockup


def selfTest():
    # use this form if fields can be hardcoded
    form = formMockup(name='Bob', job='hacker', food=['Spam', 'eggs', 'ham'])

    if form['name'].value == 'Bob':
        print('Test pass')
    else:
        print('Test fail')

    if form['food'][1].value == 'eggs':
        print('Test pass')
    else:
        print('Test fail')


if __name__ == '__main__':
    selfTest()
