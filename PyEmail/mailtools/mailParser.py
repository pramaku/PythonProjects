#!/usr/bin/python
"""
parsing and attachment extract, analyse, save e-mails.
"""

import os
import mimetypes
import sys

import email.parser
import email.header
import email.utils
from email.message import Message

from .mailTool import MailTool
from .mailTool import SilentMailTool

class MailParser(MailTool):
    """
    methods for parsing message text, attachments.

    For simple messages, the message body is always considered here to be the sole part of the mail;
    For multipart messages, the parts list includes the main message text,
    as well as all attachments;
    This allows simple messages not of type text to be handled like attachments in a UI (e.g., saved, opened);
    Message payload may also be None for some oddball part types;
    """

    def walkNamedParts(self, message):
        """

        :param message:
        :return:
        """
        for(ix, part) in enumerate(message.walk()):
            fulltype = part.get_content_type()
            maintype = part.get_content_maintype()

            if maintype == 'multipart':  # multipart/*: container
                continue
            elif fulltype == 'message/rfc822':  # skip message/rfc822
                continue  # skip all message/* too?
            else:
                filename, contype = self.partName(part, ix)
                yield (filename, contype, part)

    def partName(self, part, ix):
        """
        extract filename and content type from message part;

        :param part: message part
        :param ix: index
        :return: (filename, contentType)
        """
        filename = part.get_filename()  # filename in msg hdrs?
        contype = part.get_content_type()  # lowercase maintype/subtype
        if not filename:
            filename = part.get_param('name')  # try content-type name
        if not filename:
            if contype == 'text/plain':  # hardcode plain text ext
                ext = '.txt'             # else guesses .ksh!
            else:
                ext = mimetypes.guess_extension(contype)
            if not ext:
                ext = '.bin'  # use a generic default
            filename = 'part-%03d%s' % (ix, ext)
        return (filename, contype)

    def saveParts(self, savedir, message):
        """
        store all parts of a message as files in a local directory;
        :param savedir: directory name where the file is saved
        :param message: input message
        :return: returns [('maintype/subtype', 'filename')] list
        """

        if not os.path.exists(savedir):
            os.mkdir(savedir)

        partfiles = []

        for (filename, contype, part) in self.walkNamedParts(message):
            fullname = os.path.join(savedir, filename)
            fileobj = open(fullname, 'wb')          # use binary mode
            content = part.get_payload(decode=1)    # decode base64,qp,uu

            if not isinstance(content, bytes):      # 4E: need bytes for rb
                content = b'(no content)'           # decode=1 returns bytes,

            fileobj.write(content)                  # but some payloads None
            fileobj.close()                         # 4E: not str(content)
            partfiles.append((contype, fullname))   # for caller to open
        return partfiles

    def saveOnePart(self, savedir, partname, message):
        """
        save the given part of the message
        :param savedir: directory where the file is saved.
        :param partname: message part name
        :param message: email message
        :return: (contype, fullname)
        """
        if not os.path.exists(savedir):
            os.mkdir(savedir)

        fullname = os.path.join(savedir, partname)

        (contype, content) = self.findOnePart(partname, message)

        if not isinstance(content, bytes):  # 4E: need bytes for rb
            content = b'(no content)'  # decode=1 returns bytes,

        open(fullname, 'wb').write(content)  # but some payloads None
        return (contype, fullname)

    def partsList(self, message):
        """
        return a list of filenames for all parts of an already parsed message
        :param message: e-mail message
        :return: list of filenames
        """
        validParts = self.walkNamedParts(message)
        return [filename for (filename, contype, part) in validParts]

    def findOnePart(self, partname, message):
        """
        find and return part's content, given its name.
        :param partname: message part name
        :param message : total message.
        :return: (content type, content)
        """
        for (filename, contype, part) in self.walkNamedParts(message):
            if filename == partname:
                content = part.get_payload(decode=1)  # does base64,qp,uu
                return contype, content

    def decodedPayload(self, part, asStr=True):
        """
        decode text part bytes to Unicode str for display
        :param part: message text
        :param asStr: decode to unciode 'str' if true
        :return: the decoded payload string
        """
        payload = part.get_payload(decode=1)

        if asStr and isinstance(payload, bytes):
            encodings = []
            enchdr = part.get_content_charset()

            if enchdr:
                encodings += [enchdr]

            encodings += [sys.getdefaultencoding()]
            encodings += ['latin1', 'utf8']

            for enc in encodings:
                try:
                    payload = payload.decode(enc)
                    break
                except (UnicodeError, LookupError):
                    pass
            else:
                #some exception
                payload = '--Sorry: cannot decode Unicode text--'
        return payload

    def findMainText(self, message, asStr=True):
        """
        decode and return the payload based on the content type
        :param message: e-mail message object.
        :param asStr: decode to unciode 'str' if true
        :return: (type, decoded payload text)
        """

        #try for plain text type
        for part in message.walk():
            type = part.get_content_type()
            if type == 'text/plain':
                return type, self.decodedPayload(part, asStr)

        # try for html type
        for part in message.walk():
            type = part.get_content_type()
            if type == 'text/html':
                return type, self.decodedPayload(part, asStr)

        # try any other text type, including XML
        for part in message.walk():
            if part.get_content_maintype() == 'text':
                return part.get_content_type, self.decodedPayload(part, asStr)

        failtext = '[No text to display]' if asStr else b'[No text to display]'
        return 'text/plain', failtext

    def decodeHeader(self, rawheader):
        """
        decode and return the e-mail header
        :param rawheader: raw e-mail header data
        :return: decoded header data or same input if error in decoding.
        """

        try:
            parts = email.header.decode_header(rawheader)
            decoded = []

            for (part, enc) in parts:
                if enc == None:
                    if not isinstance(part, bytes):
                        decoded += [part]
                    else:
                        decoded += [part.decode('raw-unicode-escape')]
                else:
                    decoded += [part.decode(enc)]

            return ' '.join(decoded)
        except:
            return rawheader

    def decodeAddrHeader(self, rawheader):
        """
        decode address header, (uses 'decodeheader' internally)
        :param rawheader: raw address header
        :return: decoded header or same input if error
        """
        try:
            pairs = email.utils.getaddresses([rawheader])
            decoded = []

            for (name, addr) in pairs:
                try:
                    name = self.decodeHeader(name)
                except:
                    name = None
                joined = email.utils.formataddr(name, addr)
                decoded.append(joined)
            return ' '.join(decoded)
        except:
            return self.decodeHeader(rawheader)

    def splitAddresses(self, field):
        """
        split the address fields into a list of [name, <addr>]
        :param field: address field
        :return: list of pair of name and address or empty if error
        """
        try:
            pairs = email.utils.getaddresses([field])
            return [email.utils.formataddr(pair) for pair in pairs]
        except:
            return []

    # returned when e-mail parse fail (common error message for the class)
    errorMessage = Message()
    errorMessage.set_payload('[Unable to parse message - format error]')

    def parseHeaders(self, mailtext):
        """
        parse headers only, return root email.message.Message object
        :param mailtext: e-mail text
        :return: email.message.Message object after parse
        """
        try:
            return email.parser.Parser().parsestr(mailtext, headersonly=True)
        except:
            return self.errorMessage

    def parseMessage(self, fullText):
        """
        parse entire message, return root email.message.Message object
        payload of message object is a string if not multi part message
        payload of message object is Message objects if multi part message
        :param fullText: full e-mail text
        :return:
        """
        try:
            return email.parser.Parser().parsestr(fullText)
        except:
            return self.errorMessage

    def parseMessageRaw(self, fulltext):
        """
        parse headers only, return root email.message.Message objec
        :param fulltext: full e-mail text
        :return: email.message.Message object after parse
        """
        try:
            return email.parser.HeaderParser().parsestr(fulltext)
        except:
            return self.errorMessage