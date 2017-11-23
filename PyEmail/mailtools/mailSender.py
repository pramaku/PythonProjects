#!/usr/bin/python
"""
send messages, add e-mail attachments.
"""
import smtplib
import os
import mimetypes

import email.utils
import email.encoders

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication

# local imports
import mailconfig
from .mailTool import MailTool
from .mailTool import SilentMailTool


# some util methods
def fix_encode_base_64(msgobj):
    linelen = 76  # per MIME standards
    from email.encoders import encode_base64

    encode_base64(msgobj)
    text = msgobj.get_payload()
    if isinstance(text, bytes):
        text = text.decode('ascii')

    lines = []
    text = text.replace('\n', '')
    while text:
        line, text = text[:linelen], text[linelen:]
        lines.append(line)
    msgobj.set_payload('\n'.join(lines))


def fix_text_required(encodingName):
    from email.charset import Charset
    from email.charset import QP

    charset = Charset(encodingName)
    bodyenc = charset.body_encoding
    return bodyenc in (None, QP)


class MailSender(MailTool):
    """
    send mail: format a message, interface with an SMTP server,
    works on any machine with Python + Internet, doesn't use cmdline e-mail,
    a nonauthenticating client: see MailSenderAuth if login required to e-mail
    server
    """
    def __init__(self, smtpservername=None, tracesize=256):
        self.smtpservername = smtpservername or mailconfig.smtpservername
        self.tracesize = tracesize

    def sendMessage(self, From, To, Subj, extrahdrs, bodytext, attaches,
                    saveMailSeparator=(('=' * 80) + 'PY\n'),
                    bodytextEncoding='us-ascii',
                    attachesEncodings=None):
        """
        formats and sends an e-mail.
        saves the sent e-mail if sent sucessfully.
        arguments:
        bodytext - text part of the e-mail (assumes it is already in desired
                                                encoding.)
        attaches - list of files to be attached
        extrahdrs - list of tuples to be added (Name, Value)
        """
        # body text encoding
        if fix_text_required(bodytextEncoding):
            if not isinstance(bodytext, str):
                bodytext = bodytext.decode(bodytextEncoding)
        else:
            if not isinstance(bodytext, bytes):
                bodytext = bodytext.encode(bodytextEncoding)

        # attachments
        if not attaches:
            msg = Message()
            msg.set_payload(bodytext, charset=bodytextEncoding)
        else:
            msg = MIMEMultipart()
            self.addAttachments(msg, bodytext, attaches, bodytextEncoding,
                                attachesEncodings)

        # e-mail header encoding
        hdrenc = mailconfig.headersEncodeTo or 'utf-8'
        Subj = self.encodeHeader(Subj, hdrenc)
        From = self.encodeAddrHeader(From, hdrenc)
        To = [self.encodeAddrHeader(T, hdrenc) for T in To]
        Tos = ', '.join(To)

        # attach header to message
        msg['From'] = From
        msg['To'] = Tos
        msg['Subj'] = Subj
        msg['Date'] = email.utils.formatdate()
        recip = To

        for (name, value) in extrahdrs:
            if value:
                if name.lower() not in ['cc', 'bcc']:
                    value = self.encodeHeader(value, hdrenc)
                    msg[name] = value
                else:
                    value = [self.encodeAddrHeader(V, hdrenc) for V in value]
                    recip += value
                    if name.lower() != 'bcc':
                        msg[name] = ', '.join(value)

        # remove duplicates
        recip = list(set(recip))

        fullText = msg.as_string()

        self.trace('Sending to...' + str(recip))
        self.trace(fullText[:self.tracesize])

        # smtp connection.
        server = smtplib.SMTP_SSL(self.smtpservername)
        self.getPassword()
        self.authenticateServer(server)

        try:
            failed = server.sendmail(From, recip, fullText)
        except Exception:
            server.close()
            raise
        else:
            server.quit()

        self.saveSentMessage(fullText, saveMailSeparator)

        if failed:
            class SomeAddrsFailed(Exception):
                pass
            raise SomeAddrsFailed('Failed addrs:%s\n' % failed)
        self.trace('Send exit')

    def addAttachments(self, mainmsg, bodytext, attaches,
                       bodytextEncoding, attachesEncoding):
        """
        format a multipart message with attachments;
        use Unicode encodings for text parts if passed;
        """

        # add main text/plain part
        msg = MIMEText(bodytext, _charset=bodytextEncoding)
        mainmsg.attach(msg)

        # add attachment parts (default ascii)
        encodings = attachesEncoding or (['us-ascii'] * len(attaches))

        for (filename, fileencode) in zip(attaches, encodings):
            # skip non file items like directories
            if not os.path.isfile(filename):
                continue

            # guess content type from file extension, ignore encoding
            (contype, encoding) = mimetypes.guess_type(filename)
            if contype is None and encoding is not None:
                contype = 'application/octet-stream'
            self.trace('Adding ' + contype)

            # build sub-Message of appropriate kind
            (maintype, subtype) = contype.split('/', 1)
            if maintype == 'text':
                if fix_text_required(fileencode):
                    data = open(filename, 'r', encoding=fileencode)
                else:
                    data = open(filename, 'rb')
                msg = MIMEText(data.read(), _subtype=subtype,
                               _charset=fileencode)
                data.close()

            elif maintype == 'image':
                data = open(filename, 'rb')
                msg = MIMEImage(data.read(), _subtype=subtype,
                                _encoder=fix_encode_base64)
                data.close()

            elif maintype == 'audio':
                data = open(filename, 'rb')
                msg = MIMEAudio(data.read(), _subtype=subtype,
                                _encoder=fix_encode_base64)
                data.close()

            elif maintype == 'application':
                data = open(filename, 'rb')
                msg = MIMEApplication(data.read(), _subtype=subtype,
                                      _encoder=fix_encode_base64)
                data.close()

            else:
                data = open(filename, 'rb')
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(data.read())
                data.close()
                fix_encode_base64(msg)

            # set filename and attach to container
            basename = os.path.basename(filename)
            msg.add_header('Content-Disposition', 'attachment',
                           filename=basename)
            mainmsg.attach(msg)

    def saveSentMessage(self, fullText, saveMailSeparator):
        """
        append sent message to local file if send worked for any;
        client: pass separator used for your application, splits;
        caveat: user may change the file at same time (unlikely);
        """
        try:
            sentfile = open(mailconfig.sentmailfile, 'a',
                            encoding=mailconfig.fetchEncoding)
            if fullText[-1] != '\n':
                fullText += '\n'
            sentfile.write(saveMailSeparator)
            sentfile.write(fullText)
            sentfile.close()
        except Exception:
            self.trace('Could not save sent message')   # not fatal error

    def encodeHeader(self, headerText, unicodeencoding='utf-8'):
        try:
            headerText.encode('ascii')
        except Exception:
            try:  # make simple header.
                hdrobj = email.header.make_header([(headerText,
                                                    unicodeencoding)])
                headerText = hdrobj.encode()
            except Exception:
                pass
        return headerText

    def encodeAddrHeader(self, headerText, unicodeencoding='utf-8'):
        try:
            # split addrs + parts
            pairs = email.utils.getaddresses([headerText])
            encoded = []
            for (name, addr) in pairs:
                try:
                    name.encode('ascii')
                except UnicodeError:
                    try:
                        uni = name.encode(unicodeencoding)
                        hdr = email.header.make_header([(uni,
                                                         unicodeencoding)])
                        name = hdr.encode()
                    except Exception:
                        name = None
            joined = email.utils.formataddr((name, addr))
            encoded.append(joined)

            fullHdr = ', '.join(encoded)

            # wrap in new lines when exceeding line
            if len(fullHdr) > 72 or '\n' in fullHdr:
                fullHdr = ',\n '.join(encoded)
            return fullHdr
        except Exception:
            return self.encodeHeader(headerText)

    def authenticateServer(self, server):
        user = mailconfig.smtpuser or 'pandillapradeepkumar@gmail.com'
        server.login(user, self.getPassword(user))
        # assert False, 'Use subclass MailSenderAuth if needs authentication'

    def askSmtpPassword(self, user):
        import getpass
        prompt = 'Password for %s on %s?' % (user, self.smtpservername)
        return getpass.getpass(prompt)


# specialized sub class
class MailSenderAuth(MailSender):
    """
    use for servers that require login authorization;
    client: choose MailSender or MailSenderAuth superclass based on
    mailconfig.smtpuser setting (None?)
    Use this class if password needs to be read from file.
    Use MailSenderAuthConsole class if password needs to be read from console.
    """
    # put this in class, to get shared by all instances
    smtpPassword = None

    def __init__(self, smtpservername=None, tracesize=256):
        MailSender.__init__(self, smtpservername, tracesize)
        self.smtpUser = mailconfig.smtpuser or 'pandillapradeepkumar@gmail.com'
        # self.smtpPassword = None

    def authenticateServer(self, server):
        server.login(self.smtpUser, self.getPassword())

    def getPassword(self):
        if not self.smtpPassword:
            try:
                localfile = open(mailconfig.smtppasswdfile)
                MailSenderAuth.smtpPassword = localfile.readline()[:-1]  # 4E
                self.trace('local file password' + repr(self.smtpPassword))
            except Exception:
                # if not from file, force to use by Sub console class
                MailSenderAuth.smtpPassword = self.askSmtpPassword()

    def askSmtpPassword(self):
        assert False, 'Subclass must define method'


class MailSenderAuthConsole(MailSenderAuth):
    def askSmtpPassword(self):
        import getpass
        prompt = 'Password for %s on %s?' % (self.smtpUser,
                                             self.smtpServerName)
        return getpass.getpass(prompt)


class SilentMailSender(SilentMailTool, MailSender):
    pass
