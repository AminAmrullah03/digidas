#!/usr/bin/python

# Copyright (c) 2017, Sandeep Yadav
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the <organization> nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL SANDEEP YADAV (DAMBALLA) BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import argparse
import urllib.request, urllib.error, urllib.parse
from contextlib import closing
try:
    from importlib.resources import open_text
except ModuleNotFoundError:
    raise ModuleNotFoundError("Missing importlib.resources module. Is Python>=3.7 ?")


class InvalidDomainError (Exception):
    def __init__(self, domain, custmsg='Invalid domain entered'):
        self._custmsg = custmsg + ': ' + domain

    def __str__(self):
        return self._custmsg


class Dnspy:
    """A class for computing sub-domains and domain labels for a given
    FQDN (Fully Qualified Domain Name).

    """

    def __init__(self, update_tlds=False):
        """ Read the ETLD list provided by the user.
            Args:
                @update_tlds:   Boolean flag to allow the user to update the
                                TLD file from Mozilla source (DEFAULT_URL)
            Returns:
        """
        DEFAULT_URL = 'http://mxr.mozilla.org/mozilla-central/source/netwerk/dns/effective_tld_names.dat?raw=1'
        ETLD_FILENAME = 'mozilla_etlds.dat'

        etld_inf = open_text('dnspy.data', ETLD_FILENAME)
        self.etlds = {}

        if update_tlds:
            etld_inf.close()
            # Download the latest ETLD list
            urllib.request.urlretrieve(DEFAULT_URL, etld_inf.name)
            etld_inf = open_text('dnspy.data', ETLD_FILENAME)
            print('File updated...')

        for line in etld_inf:

            # Py3: line is of type 'bytes'; convert to ASCII string
            line = line.strip()
            # Ignore comments and whitespace lines
            if (line.startswith('//') or line == ''):
                continue

            if line[0] == '*':
                # Any hostname matches wildcard
                etld_ = line[2:].encode('idna').decode()
                if etld_ not in self.etlds:
                    self.etlds[etld_] = set()
                self.etlds[line[2:]].add('*')
            elif line[0] == '!':
                # Exceptions to the wildcard rule
                lbls = line.split('.')
                etld_ = '.'.join(lbls[1:]).encode('idna').decode()
                if etld_ not in self.etlds:
                    self.etlds[etld_] = set()
                self.etlds[etld_].add(lbls[0])
            else:
                # Else the normal case
                etld_ = line.encode('idna').decode()
                if etld_ not in self.etlds:
                    self.etlds[etld_] = set()

        etld_inf.close()
        return

    def etld(self, domain):
        """ Given a domain, get the effective top level domains.
            If domain is invalid, raise InvalidDomainError.
            Args:
                @domain:    Domain name [string]
            Returns:
                Effective top-level domain [string]
        """
        domain = domain.encode('idna').decode()
        dlabels = domain.strip().split('.')

        etld = None
        for i in range(len(dlabels)):
            etld = '.'.join(dlabels[i:])
            if etld in self.etlds:
                break
            etld = None

        # Borderline cases
        if etld is None:
            raise InvalidDomainError(domain)

        # Check for regex cases
        if ((i >= 1) and ('*' in self.etlds[etld]) and
                (('!' + dlabels[i-1]) not in self.etlds[etld])):
            etld = dlabels[i-1] + '.' + etld

        return etld

    def subdoms(self, domain, n=3):
        """ Given a qname, return a list of all subdomains.
            E.g. for 'www.google.com'

            returns ['com', 'google.com', 'www.google.com']

            Args:
                @domain:    Domain name [string]
            Returns:
                [list] of sub-domains
        """
        if n == 0:
            return []

        domain = domain.encode('idna').decode()
        etld = self.etld(domain)

        dlabels = domain[:-1*(len(etld) + 1)].split('.')
        dlabels.reverse()

        subdlst = list()
        subdlst.append(etld)

        # Number of sub-domains to return; if negative, return all
        nsubd = len(dlabels) if n < 0 else min(n - 1, len(dlabels))
        subd = etld
        for i in range(nsubd):
            if dlabels[i] == '':
                continue
            subd = dlabels[i] + '.' + subd
            subdlst.append(subd)

        return subdlst

    def domlabels(self, domain, n=3):
        """ Returns a list of domain labels at different levels.
            E.G. 'www.google.com'
            RETURNS ['com', 'google', 'www']
            Args:
                @domain:    Domain name [string]
            Returns:
                [list] of domain labels
        """
        if n == 0:
            return []

        domain = domain.encode('idna').decode()
        etld = self.etld(domain)

        dlabels = domain[:-1*(len(etld) + 1)].split('.')
        dlabels.reverse()

        lblst = list()
        lblst.append(etld)

        # Number of domain labels to return; if negative, return all
        ndl = len(dlabels) if n < 0 else min(n - 1, len(dlabels))
        for i in range(ndl):
            if dlabels[i] == '':
                continue
            lblst.append(dlabels[i])

        return lblst

    def subdom_count(self, domain):
        """ Return a tuple with the second-level domain and the count
            of all sub-domains not including the second-level domain.
            E.G. 'a.b.c.d.google.com'
            RETURNS (google.com, 4)
            Args:
                @domain:    Domain name [string]
            Returns:
                [tuple]
        """
        subdoml = self.subdoms(domain, n=-1)
        return (subdoml[1], len(subdoml[2:]))


def main(argv=sys.argv):

    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--qname', dest='qname',
                        help='The input qname')

    if len(argv) == 1:
        parser.print_help()
        return 1    # Non-zero exit

    args = parser.parse_args()
    dpy = Dnspy()

    print(str(dpy.subdoms(args.qname)))
    print(str(dpy.domlabels(args.qname)))
    print(str(dpy.subdom_count(args.qname)))


if __name__ == "__main__":
    sys.exit(main())
