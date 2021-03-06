###
# Copyright (c) 2010, bc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from sys import stderr
import re

try:
    import adns
except ImportError:
    raise callbacks.Error, \
        'The adns module is required to use this plugin. ' \
        'See README.txt.'

class Dns(callbacks.Plugin):
    """
    Look up various DNS related information for a domain name"""
    threaded = True
    _hostExpr = re.compile(utils.web._domain)
    
    def __init__(self, irc):
        self.__parent = super(Dns, self)
        self.__parent.__init__(irc)
        self.unknownReply = 'I did not understand that query.'
        self.nsconfig = ''
        self.nameservers = self.registryValue('nameservers')
        self._makeServerString(self.nameservers)
        self.dns = adns.init(adns.iflags.noautosys, 
                             stderr, self.nsconfig)

    def _makeServerString(self, servers):
        self.nsconfig = ''
        for server in servers:
            self.nsconfig += "nameserver %s\n" % server

    def _initServers(self):
        if self.nameservers != self.registryValue('nameservers'):
            self.nameservers = self.registryValue('nameservers')
            self._makeServerString(self.nameservers)
            self.dns = adns.init(adns.iflags.noautosys, 
                                 stderr, self.nsconfig)

    def _lookup(self, domain, type):
        self._initServers()
        records = self.dns.synchronous(domain, eval('adns.rr.%s' % type))
        try: adns.exception(records[0])
        except (adns.RemoteFailureError, 
                adns.LocalError, 
                adns.NotReady, 
                adns.QueryError,
                adns.RemoteConfigError, 
                adns.RemoteTempError), e:
            # 100: Inconsistent resource records in DNS
            if e[0] != 100: raise Exception(e[1])
        except (adns.NXDomain, adns.NoData):
            pass
        return records
        
    def _resolve(self, domain):
        reply = []
        self._initServers()
        records = self._lookup(domain, 'A')
        try: adns.exception(records[0])
        except (adns.RemoteFailureError, 
                adns.LocalError, adns.NotReady, 
                adns.QueryError,
                adns.RemoteConfigError, 
                adns.RemoteTempError), e:
            if e[0] != 100: raise Exception(e[1])
        except (adns.NXDomain, adns.NoData):
            pass
        if records[3]:
            for record in records[3]:
                reply.append('%s' % record)
            return ', '.join(reply)
        else:
            return None

    def aa(self, irc, msg, args, domain):
        """<domain>
        Look up A record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            try:   records = self._lookup(domain, 'A')
            except Exception, e:
                irc.error(e, Raise=True)
            if records[3]:
                for record in records[3]:
                    reply.append('%s' % record)
                irc.reply(', '.join(reply))
            else: 
                irc.reply('Nothing found.')
        else:
            irc.error(self.unknownReply)

    aa = thread(wrap(aa, [('matches', _hostExpr, 'Invalid domain')]))

    def ptr(self, irc, msg, args, ip):
        """<ip>
        Find PTR record for an IP address"""
        domain = "%s.in-addr.arpa" % '.'.join(reversed(ip.split('.')))
        reply = []
        try:   records = self._lookup(domain, 'PTR')
        except Exception, e:
            irc.error(e, Raise=True)
        if records[3]:
            for record in records[3]:
                reply.append('%s' % record)
            irc.reply(', '.join(reply))
        else:
            irc.reply('Nothing found.')

    ptr = thread(wrap(ptr, ['ip']))

    def cname(self, irc, msg, args, domain):
        """<domain>
        Look up CNAME record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            try:   records = self._lookup(domain, 'CNAME')
            except Exception, e:
               irc.error(e, Raise=True)
            if records[3]:
                for idx, record in enumerate(records[3]):
                    reply.append('%s' % record.lower())
                    try:   aa = self._resolve(record)
                    except Exception, e:
                        irc.error(e, Raise=True)
                    if aa: reply[idx] += ' (%s)' % aa
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.error(self.unknownReply)

    cname = thread(wrap(cname, [('matches', _hostExpr, 'Invalid domain')]))

    def mx(self, irc, msg, args, domain):
        """<domain>
        Look up MX record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            try:   records = self._lookup(domain, 'MX')
            except Exception, e:
                irc.error(e, Raise=True)
            if records[3]:
                for record in records[3]:
                    if record[1][2]:
                        mxip = record[1][2][0][1]
                    # Determine if returned name is actually a CNAME                    
                    else:
                        try: cname_record = self._lookup(record[1][0], 'CNAME')
                        except Exception, e:
                            irc.error(e, Raise=True)
                        if cname_record[3]:
                            mxip = 'CNAME for %s' % cname_record[3][0]
                            # Find IP for CNAME
                            try:   aa = self._resolve(cname_record[3][0])
                            except Exception, e:
                                irc.error(e, Raise=True)
                            if aa: mxip += ' (%s)' % aa
                        else:
                            mxip = 'Unknown'
                    reply.append(('%s %s (%s)' % 
                        (record[0], record[1][0].lower(), mxip)))
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(self.unknownReply)
    
    mx = thread(wrap(mx, [('matches', _hostExpr, 'Invalid domain')]))

    def ns(self, irc, msg, args, domain):
        """<domain>
        Look up NS records for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            try:   records = self._lookup(domain, 'NS')
            except Exception, e:
                irc.error(e, Raise=True)
            if records[3]:
                for record in records[3]:
                    reply.append('%s (%s)' % 
                        (record[0].lower(), record[2][0][1]))
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(self.unknownReply)
    
    ns = thread(wrap(ns, [('matches', _hostExpr, 'Invalid domain')]))

    def txt(self, irc, msg, args, domain):
        """<domain>
        Look up TXT records for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            try:   records = self._lookup(domain, 'TXT')            
            except Exception, e:
                irc.error(e, Raise=True)
            if records[3]:
                for record in records[3]:
                    reply.append(record[0])
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.error(self.unknownReply)

    txt = thread(wrap(txt, [('matches', _hostExpr, 'Invalid domain')]))

Class = Dns


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
