#!/usr/bin/python
"""
pymail2 - simple console email interface client in Python.
this version uses the mailtools package, which in turn uses poplib,
smtplib, and the email package for parsing and composing emails
displays first text part of mails, not the entire full text.
fetches just mail headers initially, using the TOP command
"""

import mailconfig
import mailtools

from pymail import inputMessage

mailcache = {}

helptext = """
Available commands:
i    - index display
l n? - list all messages (or just message n)
d n? - mark all messages for deletion (or just message n)
s n? - save all messages to a file (or just message n)
m    - compose and send a new mail message
q    - quit pymail
?    - display this help text
"""

def showIndex(msgList, msgSizes, chunk=5):
    count = 0
    for (msg, size) in zip(msgList, msgSizes):
        count += 1
        print('%d:\t%d bytes' % (count, size))

        for hdr in ('From', 'To', 'Date', 'Subject'):
            print('\t%-8s=>%s' % (hdr, msg.get(hdr, '(unknown)')))

        if count % chunk == 0:
            input('[Press Enter key]')


def fetchMessage(msgNum):
    try:
        fulltext = mailcache[msgNum]
    except KeyError:
        fulltext = fetcher.downloadMessage(msgNum)
        mailcache[msgNum] = fulltext
    return fulltext


def showMessage(msgNum, msgList):
    if 1 <= msgNum <= len(msgList):
        fulltext = fetchMessage(msgNum)
        message = parser.parseMessage(fulltext)
        ctype, maintext = parser.findMainText(message)
        print('-' * 79)
        print(maintext.rstrip() + '\n')
        print('-' * 79)
    else:
        print('Bad message number - ', msgNum)


def saveMessage(msgNum, mailfile, msgList):
    if 1 <= msgNum <= len(msgList):
        fulltext = fetchMessage(msgNum)
        localfile = open(mailfile, 'a', mailconfig.fetchEncoding)
        localfile.write('\n' + fulltext + '-' * 80 + '\n')
        localfile.close()
    else:
        print('Bad message number - ', msgNum)


def sendMessage():
    From, To, Subj, text = inputMessage()
    sender.sendMessage(From, To, Subj, [], text, attaches=None)


def deleteMessages(toDelete, verify=True):
    print('To be deleted:', toDelete)
    if verify and input('Delete?')[:1] not in ['y', 'Y']:
        print('Delete cancelled.')
    else:
        fetcher.deleteMessages(toDelete)


def msgnum(command):
    try:
        return int(command.split()[1])
    except:
        return -1


def interact(msgList, msgSizes, mailfile):
    showIndex(msgList, msgSizes)

    toDelete = []

    while True:
        try:
            command = input('[Pymail] Action? (i, l, d, s, m, q, ?) ')
        except EOFError:
            command = 'q'

        if not command:
            command = '*'

        if command == 'q':
            break

        elif command[0] == 'i':
            showIndex(msgList, msgSizes)

        elif command[0] == 'l':
            if len(command) == 1:
                for i in range(1, len(msgList) + 1):
                    showMessage(i, msgList)
            else:
                showMessage(msgnum(command), msgList)

        elif command[0] == 's':
            if len(command) == 1:
                for i in range(1, len(msgList) + 1):
                    saveMessage(i, mailfile, msgList)
            else:
                saveMessage(msgnum(command), mailfile, msgList)

        elif command[0] == 'd':
            if len(command) == 1:
                toDelete = range(1, len(msgList) + 1)
            else:
                delnum = msgnum(command)
                if (1 <= delnum <= len(msgList)) and (delnum not in toDelete):
                    toDelete.append(delnum)
                else:
                    print('Bad message number')

        elif command[0] == 'm':
            try:
                sendMessage()
            except:
                print('Error - mail not sent')

        elif command[0] == '?':
            print(helptext)

        else:
            print('What? -- type "?" for commands help')

    return toDelete


def main():
    global fetcher, parser, sender

    mailserver = mailconfig.popservername
    mailuser = mailconfig.popusername
    mailfile = mailconfig.savemailfile

    fetcher = mailtools.MailFetcherConsole(mailserver, mailuser)
    parser = mailtools.MailParser()
    sender = mailtools.MailSenderAuthConsole()

    def progress(i, maxmsgs):
        print(i, 'of', maxmsgs)

    hdrsList, msgSizes, ignore = fetcher.downloadAllHeaders(progress)
    msgList = [parser.parseHeaders(hdrtext) for hdrtext in hdrsList]

    print('[Pymail email client]')
    toDelete = interact(msgList, msgSizes, mailfile)

    if toDelete:
        deleteMessages(toDelete)

if __name__ == '__main__':
    main()
