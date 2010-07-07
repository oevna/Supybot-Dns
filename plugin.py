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

import adns
import re

class Dns(callbacks.Plugin):
    """
    Look up various DNS related information for a domain name"""
    threaded = True

    dns = adns.init()
    unknownReply = 'I did not understand that query.'
    
    def _lookup(self, domain, type):
        return self.dns.synchronous(domain, eval('adns.rr.%s' % type))
        
    def aa(self, irc, msg, args, domain):
        """<domain>
        Look up A record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            records = self._lookup(domain, 'A')
            if records[3]:
                for record in records[3]:
                    reply.append('%s' % record)
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(self.unknownReply)

    def cname(self, irc, msg, args, domain):
        """<domain>
        Look up CNAME record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            records = self._lookup(domain, 'CNAME')
            if records[3]:
                for record in records[3]:
                    reply.append('%s' % record)
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(self.unknownReply)


    def mx(self, irc, msg, args, domain):
        """<domain>
        Look up MX record for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            records = self._lookup(domain, 'MX')
            if records[3]:
                for record in records[3]:
                    if record[1][2]:
                        mxip = record[1][2][0][1]
                    # Determine if returned name is actually a CNAME                    
                    else:
                        cname_record = self._lookup(record[1][0], 'CNAME')
                        if cname_record[3]:
                            mxip = 'CNAME for %s' % cname_record[3][0]
                        else:
                            mxip = 'Unknown'
                    reply.append(('%s (%s)' % (record[1][0], mxip)))
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(unknownReply)

    def ns(self, irc, msg, args, domain):
        """<domain>
        Look up NS records for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            records = self._lookup(domain, 'NS')
            if records[3]:
                for record in records[3]:
                    reply.append('%s (%s)' % (record[0], record[2][0][1]))
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(unknownReply)

    def txt(self, irc, msg, args, domain):
        """<domain>
        Look up TXT records for a domain"""
        domain = domain.group(0)
        if domain is not None:
            reply = []
            records = self._lookup(domain, 'TXT')            
            if records[3]:
                for record in records[3]:
                    reply.append(record[0])
                irc.reply(', '.join(reply))
            else:
                irc.reply('Nothing found.')
        else:
            irc.reply(self.unknownReply)

    _hostExpr = re.compile(r'^[a-z0-9][a-z0-9\.-]*\.[a-z]{2,3}$', re.I)
    aa     = wrap(aa,    [('matches', _hostExpr, 'Invalid domain (hopefully)')])
    cname  = wrap(cname, [('matches', _hostExpr, 'Invalid domain (hopefully)')])
    mx     = wrap(mx,    [('matches', _hostExpr, 'Invalid domain (hopefully)')])
    ns     = wrap(ns,    [('matches', _hostExpr, 'Invalid domain (hopefully)')])
    txt    = wrap(txt,   [('matches', _hostExpr, 'Invalid domain (hopefully)')])

Class = Dns


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
