#!/usr/bin/python
"""
common superclasses: used to turn trace messages on/off

Usage:
derive from MailTool and use 'trace' method to enable tracing
derive from SielntMailTool and use trace to ignore all traces
"""


class MailTool:
    def trace(self, message):
        print(message)


class SilentMailTool:
    def trace(self, message):
        pass


# self test
if __name__ == '__main__':
    class MyMailTool(MailTool):
        pass
    tool = MyMailTool()
    tool.trace('Test log from mailTool.py')

    class MySilentMailTool(SilentMailTool):
        pass

    tool = MySilentMailTool()
    tool.trace('Test log from mailTool.py')
