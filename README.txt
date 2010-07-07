Dns provides methods to make DNS queries about domain names.

The Python adns module is required. On Debian-like distrubitions, 
`sudo apt-get install python-adns` should be all you need to do.

Available commands:
   
   cname - CNAME record(s)
      aa - Find A record(s)
      mx - MX record(s) (Finds CNAME if needed)
      ns - NS record(s)
     txt - TXT record(s)

All commands should accept single, valid domain name.

