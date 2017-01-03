#!/usr/bin/python
"""
script to test the mailtools package module.
"""

import sys
sys.path.append('..')
import mailconfig
print('using config file :', mailconfig.__file__, ' for testing')

from mailtools import MailFetcherConsole
from mailtools import MailSender, MailSenderAuthConsole
from mailtools import MailParser

# use below if selftest.py is inside the mailtools directory
# from mailFetcher import MailFetcherConsole
# from mailSender import MailSender, MailSenderAuthConsole
# from mailParser import MailParser


# callback method used n testing
def status(*args):
    print(args)


def send():
    """
    Sends an test e-mail using mailtools package 'mailSender' module
    :return: None
    """
    if not mailconfig.smtpuser:
        sender = MailSender(tracesize=5000)
    else:
        sender = MailSenderAuthConsole(tracesize=5000)

    # send the e-mail
    sender.sendMessage(From = mailconfig.myaddress,
                        To = [mailconfig.myaddress],
                        Subj = 'testing mailtools package',
                        extrahdrs = [('X-Mailer', 'mailtools')],
                        bodytext = 'Here is my source code\n',
                        attaches = ['selftest.py'],
                        )

    # other tests to try

    # bodytextEncoding='utf-8',
    # attachesEncodings=['latin-1'], # inspect text headers
    # attaches=['monkeys.jpg'])      # verify Base64 encoded
    # to='i18n addr list...',       # test mime/unicode headers


def fetch():
    """
    Fetches some e-mail to test mailtools package 'mailFetcher' module
    :return: None
    """

    # Fetch an e-mail
    fetcher = MailFetcherConsole()

    hdrs, sizes, loadedall = fetcher.downloadAllHeaders(status)

    # load header
    for num, hdr in enumerate(hdrs[:2]):
        print(hdr)

        # if requested then e-mail.
        if input('load mail?') in ['y', 'Y']:
            print(fetcher.downloadMessage(num + 1).rstrip(), '\n', '-' * 70)


def parse():
    """
    Parse some e-mail to test mailtools package 'mailParse' module
    :return: None
    """
    # parsing e-mail
    # first fetch the e-mails

    fetcher = MailFetcherConsole()
    hdrs, sizes, loadedall = fetcher.downloadAllHeaders(status)
    # load recent 2 e-mails
    last2 = len(hdrs)-2
    msgs, sizes, loadedall = fetcher.downloadAllMessages(status, loadfrom=last2)
    for msg in msgs:
        print(msg[:200], '\n', '-'*70)

    parser = MailParser()

    for i in [0]:  # or [0, len(msgs)] for all messages
        fulltext = msgs[i]
        message = parser.parseMessage(fulltext)
        ctype, maintext = parser.findMainText(message)
        print('Parsed:', message['Subject'])
        print(maintext)

if __name__ == '__main__':
    print('Start testing mailtools package')

    while True:
        print('1 - Send email')
        print('2 - Fetch email')
        print('3 - Parse email')
        print('Q - quit')

        option = input('Choose any of the above option>')

        if option == '1':
            send()
        elif option == '2':
            fetch()
        elif option == '3':
            parse()
        elif option in ['Q', 'q']:
            sys.exit(0)
        else:
            continue

        print('-' * 100)
