#!/usr/bin/python
"""
pymail - a simple console email interface client in Python; uses Python
poplib module to view POP email messages, smtplib to send new mails, and
the email package to extract mail headers and payload and compose mails;
"""

import poplib
import smtplib
import email.utils
import mailconfig
import sys

from email.parser import Parser
from email.message import Message

fetchEncoding = mailconfig.fetchEncoding


def decodeToUnicode(messageBytes, fetchEncoding=fetchEncoding):
    """
    decode fetched bytes to str Unicode string for display or parsing;
    use global setting (or by platform default, hdrs inspection, intelligent guess);
    in Python 3.2/3.3, this step may not be required: if so, return message intact;
    """
    return [line.decode(fetchEncoding) for line in messageBytes]


def splitAddrs(field):
    """
    split address list on commas, allowing for commas in name parts
    """
    pairs = email.utils.getaddresses([field])                   # [(name,addr)]
    return [email.utils.formataddr(pair) for pair in pairs]     # [name <addr>]


def inputMessage():
    From = input('From?').strip()
    To   = input('To?').strip()
    To   = splitAddrs(To)
    Subj = input('Subject?').strip()
    print('Type message text, end with line="."')
    text = ''
    while True:
        line = sys.stdin.readline()
        if line == '.\n':
            break
        text += line
    return (From, To, Subj, text)


def sendMessage():
    """
    sends email using STMP
    gets the deatils from user (see 'inputMessage' method)
    """
    From, To, Subj, text = inputMessage()
    msg = Message()
    msg['From'] = From
    msg['To'] = ', '.join(To)
    msg['Subject'] = Subj
    msg['Date'] = email.utils.formatdate()
    msg.set_payload(text)

    conn = smtplib.SMTP_SSL(mailconfig.smtpservername)
    try:
        username = mailconfig.popusername
        conn.login(username, input('Password for %s:' % username))
        failed = conn.sendmail(From, To, str(msg))
    except:
        print('Error in sending email:', sys.exc_info()[1])
    else:
        if failed:
            print('Failed to send email:', failed)


def connect(server, user, passwd):
    """
    Connects to the given POP server
    returns the connection object
    """
    print('Connecting...')
    try:
        conn = poplib.POP3_SSL(server)
        conn.user(user)
        conn.pass_(passwd)
        print(conn.getwelcome())
        return conn
    except:
        print('Error in connecting to', server, sys.exc_info()[1])
        return None


def loadMessages(server, user, passwd, loadFrom=1):
    """
    loads the emails into memory
    use 'loadFrom' to load emails from specific number
    returns list of emails (decoded to str from bytes)
    """
    conn = connect(server, user, passwd)
    if conn:
        try:
            # print(conn.list())                  #to avoid huge output
            (msgCount, msgBytes) = conn.stat()
            print('There are', msgCount, 'mail messages in', msgBytes, 'bytes')
            print('Retrieving...')

            # e-mail's could be huge, for time being just load last 5 emails
            if msgCount > 5:
                loadFrom = msgCount - 5
            msgList = []
            for i in range(loadFrom, msgCount+1):
                (hdr, msg, octets) = conn.retr(i)
                msg = decodeToUnicode(msg)
                msgList.append('\n'.join(msg))
        finally:
            conn.quit()
        assert len(msgList) == (msgCount - loadFrom) + 1    # check if all emails are loaded
        return msgList
    else:
        return None


def deleteMessages(server, user, passwd, toDelete, verify=True):
    """
    deletes the emails for the given list of message numbers
    """
    print('To be delete:', list(toDelete))
    if verify and input('Delete:?')[:1] not in ['y', 'Y']:
        print('Delete cancelled.')
    else:
        conn = connect(server, user, passwd)
        if conn:
            print('Deleting messages from server...')
            for msgNum in toDelete:
                conn.dele(msgNum)
        else:
            print('Error deleting email:', sys.exc_info()[1])


def showIndex(msgList):
    """
    display message headers for the given messages
    """
    count = 0                                                  # show some mail headers
    for msgtext in msgList:
        msghdrs = Parser().parsestr(msgtext, headersonly=True) # expects str in 3.1
        count += 1
        print('%d:\t%d bytes' % (count, len(msgtext)))

        for hdr in ('From', 'To', 'Date', 'Subject'):
            try:
                print('\t%-8s=>%s' % (hdr, msghdrs[hdr]))
            except KeyError:
                print('\t%-8s=>(unknown)' % hdr)
        if count % 5 == 0:
            input('[Press Enter key]')


def showMessage(msgNum, msgList):
    """
    display the emil content for the given msgnum in the list
    the list is loaded using 'loadMessages'
    """
    if 1 <= msgNum <= len(msgList):
        print('-' * 79)
        msg = Parser().parsestr(msgList[msgNum - 1])
        content = msg.get_payload()
        if isinstance(content, str):
            content = content.rstrip() + '\n'
        print(content)
        print('-' * 79)
    else:
        print('Bad message number:', msgNum)


def saveMessage(msgNum, mailFile, msgList):
    """
    save the emil contents to the given file
    """
    if 1 <= msgNum <= len(msgList):
        savefile = open(mailfile, 'a', encoding=mailconfig.fetchEncoding)
        savefile.write('\n' + msgList[msgNum - 1] + '-'*80 + '\n')
    else:
        print('Bad message number:', msgNum)


def msgnum(command):
    try:
        return int(command.split()[-1])
    except:
        return None

helpText = """
Available commands:
i    - index display
l n? - list all messages (or just message n)
d n? - mark all messages for deletion (or just message n)
s n? - save all messages to a file (or just message n)
m    - compose and send a new mail message
q    - quit pymail
?    - display this help text
"""


def interact(msgList, mailfile):
    showIndex(msgList)
    toDelete = []
    while True:
        try:
            command = input('[PyMail] Action? (i, l, d, s, m, q, ?) ')
        except EOFError:
            command = 'q'
        if not command:
            command = '*'

        if command == 'q':          #quit
            break
        elif command == 'i':        #index
            showIndex(msgList)
        elif command[0] == 'l':     #list
            if len(command) == 1:
                for i in range(1, len(msgList) + 1):
                    showMessage(i, msgList)
            else:
                showMessage(msgnum(command), msgList)
        elif command[0] == 's':             # save
            if len(command) == 1:
                for i in range(1, len(msgList)+1):
                    saveMessage(i, mailfile, msgList)
            else:
                saveMessage(msgnum(command), mailfile, msgList)
        elif command[0] == 'd':     #delete
            if len(command) == 1:
                toDelete = list(range(1, len(msgList)+1))
            else:
                delNum = msgnum(command)
                if ((1 <= delNum <= len(msgList)) and (delNum not in toDelete)):
                    toDelete.append(toDelete)
                else:
                    print('Bad message number')
        elif command[0] == 'm':      #send email
            sendMessage()
        elif command == '?':
            print(helpText)
        else:
            print('What? -- type "?" for commands help')
    return toDelete

# self testing
if __name__ == '__main__':
    import getpass
    import mailconfig
    mailserver = mailconfig.popservername
    mailuser   = mailconfig.popusername
    mailfile   = mailconfig.savemailfile
    mailpswd   = getpass.getpass('Password for %s?' % mailserver)
    print('[Pymail email client]')

    msgList = loadMessages(mailserver, mailuser, mailpswd)
    if msgList:
        toDelete = interact(msgList, mailfile)
        if toDelete:
            deleteMessages(mailserver, mailuser, mailpswd, toDelete)
    else:
        print('Error in loading messages, cannot proceed')

    # user quit
    print('Bye')
