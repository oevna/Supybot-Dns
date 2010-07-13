Dns provides methods to make DNS queries about domain names.

The Python adns module is required. On Debian-like distributions, 
`sudo apt-get install python-adns` should be all you need to do.

The adns library makes use of nameservers listed in /etc/resolv.conf.

Available commands:
   
   cname - CNAME record(s)
      aa - Find A record(s)
     ptr - Find PTR record
      mx - MX record(s) (Finds CNAME if needed)
      ns - NS record(s)
     txt - TXT record(s)

All commands should accept single, valid domain name.

Getting a copy:

git clone git@github.com:oevna/Supybot-Dns.git && mv Supybot-Dns Dns

Then drop Dns into a valid Supybot "additional" plugins location:

/msg bot config supybot.directories.plugins

