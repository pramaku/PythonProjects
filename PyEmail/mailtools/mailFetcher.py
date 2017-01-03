#!/usr/bin/python
"""
retrieve, delete, match mail from a POP server
"""

import poplib
import sys

import mailconfig

from .mailParser import MailParser             # script dir, pythonpath, changes

from .mailTool import MailTool
from .mailTool import SilentMailTool

class DeleteSynchError(Exception):
    pass

class TopNotSupported(Exception):
    pass

class MessageSynchError(Exception):
    pass
    
class MailFetcher(MailTool):
    """
    fetch mail: connect, fetch headers+mails, delete mails, works on any machine with Python + Internet,
    subclass me to cache implemented with the POP protocol,
    Supporting IMAP requires new class;
    """
    def __init__(self, popserver=None, popuser=None, poppasswd=None, hastop=True):
        self.popServer   = popserver or mailconfig.popservername
        self.popUser     = popuser or mailconfig.popusername
        self.srvrHasTop  = hastop
        self.popPassword = poppasswd  #if None, ask user before connecting.
    
    def connect(self):
        self.trace('Connecting...')
        if not self.popPassword:
            self.popPassword = self.getPassword()
        
        server = poplib.POP3_SSL(self.popServer)
        server.user(self.popUser)
        server.pass_(self.popPassword)
        server.trace(server.getwelcome())
        return server
    
    #get the encoding from the clients mailconfig(sys.path)
    fetchEncoding = mailconfig.fetchEncoding
    
    def decodeFullText(self, messageBytes):
        """
        Decode full fetched mail text bytes to str Unicode string,
        Decoding is done at done at fetch, for later display or parsing.
        Decode with per-class or per-instance setting, or common types.
        Encoding type could also be found from headers inspection, or intelligent guess from structure.
        messageBytes - list of lines of message text.
        """
        text = None
        
        #try different encoding types
        kinds  = [self.fetchEncoding]
        kinds += ['ascii', 'latin1', 'utf8']
        kinds += [sys.getdefaultencoding()]
        
        #remove duplicates
        kinds = list(set(kinds))
        
        for encoding in kinds:
            try:
                text = [line.decode(encoding) for line in messageBytes]
                break
            except (UnicodeError, LookupError):
                pass
                
        if text == None:
            #encoding failed, return hdr + errmsg
            blankline = messageBytes.index(b'')
            hdrsonly = messageBytes[:blankline]
            commons = ['ascii', 'latin1', 'utf8']
            for encoding in commons:
                try:
                    text = [line.decode(encoding) for line in hdrsonly]
                    break
                except UnicodeError:
                    pass
            else:
                try:
                    text = [line.decode() for line in hdrsonly]
                except UnicodeError:
                    text = ['From: (sender of unknown Unicode format headers)']
            text += ['', '--Sorry: mailtools cannot decode this mail content!--']
        return text
        
    def downloadMessage(self, msgnum):
        """
        load full raw text of one mail msg, given its POP relative msgnum,
        caller must parse content, (raw msg is returned)
        """
        self.trace('load message ' + str(msgnum))
        
        server = self.connect()
        try:
            resp, msglines, respz = server.retr(msgnum)
        finally:
            server.quit()
        msglines = self.decodeFullText(msglines)
        return '\n'.join(msglines)
        
        
    def downloadAllHeaders(self, progress=None, loadfrom=1):
        """
        get sizes, raw header text only, for all or new msgs
        begins loading headers from message number 'loadfrom'
        use 'downloadMessage' to get a full msg text later.
        'progress' is a call back function called with (count, total) for each messge.
        returns: [headers text], [mail sizes], loadedfull?
        """
        if not self.srvrHasTop:
            return self.downloadAllMessages(progress, loadfrom)
        else:
            self.trace('Loading headers..')
            fetchLimit = mailconfig.fetchlimit
            server = self.connect()      #mailbox is locked now.
            try:
                resp, msginfos, respsz = server.list()
                msgCount = len(msginfos)
                msginfos = msginfos[loadfrom-1:]
                allsizes = [int(x.split()[1]) for x in msginfos]
                allhdrs  = []
                
                for msgnum in range(loadfrom, msgCount+1):
                    if progress:
                        progress(msgnum, msgCount)
                    if fetchLimit and (msgnum <= msgCount - fetchLimit):
                        #add dummy header
                        hdrtext = 'Subject: --mail skipped--\n\n'
                        allhdrs.append(hdrtext)
                    else:
                        #retr the hdr content
                        resp, hdrlines, respsz = server.top(msgnum, 0)
                        hdrlines = self.decodeFullText(hdrlines)
                        allhdrs.append('\n'.join(hdrlines))
            finally:
                #unlock irrespective of events
                server.unlock()
            #check to see if all the message hdrs are read.
            assert(len(allhdrs) == len(allsizes))
            
            self.trace('load headers exit')
            loadedFull = True if fetchLimit else False
            return allhdrs, allsizes, loadedFull
            
    def downloadAllMessages(self, progress=None, loadfrom=1):
        """
        load full message text from all all messages starting from 'loadFrom'
        'progress' is a callback function called with (msgnum , total) for every message.
        the message content is decoded using 'decodeFullText' method.
        returns [mails text], [mail sizes], loadedfull?
        """
        self.trace('loading full messages')
        fetchlimit = mailconfig.fetchlimit
        server = self.connect()
        
        try:
            (msgCount, msgBytes) = server.stat()
            allmsgs = []
            allsizes = []
            for i in range(loadfrom, msgCount+1):
                if progress:
                    progress(i, msgCount)
                if fetchlimit and (i <= msgCount - fetchlimit):
                    mailtext = 'Subject: --mail skipped--\n\nMail skipped.\n'
                    allmsgs.append(mailtext)
                    allsizes.append(len(mailtext))
                else:
                    (resp, message, respsz) = server.retr(i)
                    message = self.decodeFullText(message)
                    allmsgs.append(message)
                    allsizes.append(len(respsz))   #size differs after decoding.
        finally:
            server.quit()
        loadedFull = True if fetchlimit else False
        return allmsgs, allsizes, loadedFull
    
    def deleteMessages(self, msgnums, progress=None):
        """
        delete messages from the inbox.
        expects that the inbox is changed in the middle
        'progess' callback method is called for each message
        risk to use if msgnums not in sync with inbox ( use 'deleteMessagesSafely' )
        """
        self.trace("deleting e-mails")
        server = self.connect()
        try:
            for (i, msgnum) in enumerate(msgnums):
                if progress:
                    progress(i+1, msgnum)
                server.delete(msgnum)
        finally:
            server.quit()

    def deleteMessagesSafely(self, msgnums, synchHdrs, progress=None):
        """
        delete multiple msgs off server, but use TOP fetches to
        check for a match on each msg's header part before deleting;
        fails if server is not supported with 'TOP'.

        use if the mail server might change the inbox since the email index was last fetched,
        thereby changing POP relative message numbers. this can happen if email is deleted in
        a different client.

        'synchHdrs' must be a list of already loaded mail hdrs text,corresponding to selected 'msgnums'.
        raises exception if any out of synch with the email server.

        'progress' - callback called for each message deletion.
        :return: None.
        """
        if not self.srvrHasTop:
            raise TopNotSupported('Safe delete cancelled')

        self.trace('deleting mails safely')

        errmsg  = 'Message %s out of synch with server.\n'
        errmsg += 'Delete terminated at this message.\n'
        errmsg += 'Mail client may require restart or reload.'

        server = self.connect()
        try:
            (msgCount, msgBytes) = server.stat()
            for (ix, msgnum) in enumerate(msgCount):
                if progress:
                    progress(ix + 1, len(msgnums))
                if msgnum > msgCount:
                    raise DeleteSynchError(errmsg % msgnum)
                resp, hdrlines, respsz = server.top(msgnum, 0)
                hdrlines = self.decodeFullText(hdrlines)
                msghdrs = '\n'.join(hdrlines)
                if not self.headersMatch(msghdrs, synchHdrs[msgnum - 1]):
                    raise DeleteSynchError(errmsg % msgnum)
                else:
                    server.dele(msgnum)
        finally:
            server.quit()
    
    def checkSyncError(self, synchHeaders):
        """
        check to see if already loaded hdrs text in 'synchHeaders' list matches
        what is on the server, using the TOP command in POP to fetch headers text.

        use this mthod if inbox can change due to deletes in other client,
        or automatic action by email server.

        raises except if out of synch, or error while talking to server.


        :param synchHeaders: list of inbox message headers.d
        :return: None
        """
        self.trace('synch check')
        errormsg = 'Message index out of synch with mail server.\n'
        errormsg += 'Mail client may require restart or reload.'

        server = self.connect()

        try:
            lastmsgnum = len(synchHeaders)
            (msgCount, msgBytes) = server.stat()

            if lastmsgnum > msgCount:
                raise MessageSynchError(errormsg)

            if self.srvrHasTop:
                resp, hdrlines, respsz = server.top(lastmsgnum, 0)
                hdrlines = self.decodeFullText(hdrlines)
                lastmsghdrs = '\n'.join(hdrlines)
                if not self.headersMatch(lastmsghdrs, synchHeaders[:-1]):
                    raise MessageSynchError(errormsg)
        finally:
            server.quit()
    
    def headersMatch(self, hdrtext1, hdrtext2):
        """
        First try simple string match.
        some servers add a "Status:" header that changes over time.

        :param hdrtext1: e-mail header text to compare
        :param hdrtext2: e-mail header text to compare
        :return: True if the headers match else False
        """

        if hdrtext1 == hdrtext2:
            self.trace('Same headers text')
            return True

        # try match without status lines
        split1 = hdrtext1.splitlines()
        split2 = hdrtext2.splitlines()
        strip1 = [line for line in split1 if not line.startswith('Status:')]
        strip2 = [line for line in split2 if not line.startswith('Status:')]

        if strip1 == strip2:
            self.trace('Same without Status')
            return True

        # try mismatch by message-id headers if either has one
        msgid1 = [line for line in split1 if line[:11].lower() == 'message-id:']
        msgid2 = [line for line in split2 if line[:11].lower() == 'message-id:']
        if (msgid1 or msgid2) and (msgid1 != msgid2):
            self.trace('Different Message-Id')
            return False

        # try full hdr parse and common headers if msgid missing or trash
        tryheaders = ('From', 'To', 'Subject', 'Date')
        tryheaders += ('Cc', 'Return-Path', 'Received')

        msg1 = MailParser().parseHeaders(hdrtext1)
        msg2 = MailParser().parseHeaders(hdrtext2)

        for hdr in tryheaders:
            if msg1.get_all(hdr) != msg2.get_all(hdr):
                self.trace('Diff common headers')
                return False

        # all common hdrs match and don't have a diff message-id
        self.trace('Same common headers')
        return True

    def getPassword(self):
        """
        read the password from the file or subclass method
        :return: the pop password.
        """
        try:
            localfile = open(mailconfig.poppasswdfile)
            return localfile.readline()[:-1]
        except:
            return self.askPopPassword()
    
    def askPopPassword(self):
        assert False, 'Subclass must define method'

class MailFetcherConsole(MailFetcher):
    def askPopPassword(self):
        """
        prompt the user for pop password.
        :return: ppop password.
        """
        import getpass
        prompt = 'Password for %s on %s?' % (self.popUser, self.popServer)
        return getpass.getpass(prompt)

class SilentMailFetcher(SilentMailTool, MailFetcher):
    """
    MailFetcher with supressed trace.
    """
    pass
