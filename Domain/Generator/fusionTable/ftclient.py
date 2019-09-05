# -*- coding: utf-8 -*-
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Fusion Tables client library."""


import http.cookiejar
import csv
import getpass
import os
import time
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse


class FTClient(object):
    """Fusion Table SQL API wrapper."""
  
    def __init__(self, auth_token):
        self.ft_host = 'http://tables.googlelabs.com'
        self.api_path = '/api/query'
        self.auth_token = auth_token
  
    def runGetQuery(self, query):
        """Issue a GET query to the Fusion Tables API and return the result."""
        encoded_query_params = urllib.parse.urlencode({'sql': query})
        path = self.ft_host + self.api_path + '?' + encoded_query_params
        data = ''
        headers = {
            'Authorization': 'GoogleLogin auth=' + self.auth_token,
        }
        serv_req = urllib.request.Request(path, data, headers)
        serv_resp = urllib.request.urlopen(serv_req)
        serv_resp_body = serv_resp.read()
    
        return serv_resp_body
  
    def runPostQuery(self, query):
        """Issue a POST query to the Fusion Tables API and return the result."""
        path = self.ft_host + self.api_path
        data = urllib.parse.urlencode({'sql': query})
        headers = {
            'Authorization': 'GoogleLogin auth=' + self.auth_token,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    
        # Debug code -- uncomment if you need to see what's on the wire
        # h = urllib2.HTTPHandler(debuglevel=1)
        # opener = urllib2.build_opener(h)
        # urllib2.install_opener(opener)
    
        serv_req = urllib.request.Request(path, data, headers)
        serv_resp = urllib.request.urlopen(serv_req)
        serv_resp_body = serv_resp.read()
    
        return serv_resp_body
  
    def createTable(self, table_name, column_names_and_types):
        """Creates a table in Fusion Tables and returns the table ID."""
        column_defs = ', '.join(["'%s':%s" % c for c in column_names_and_types])
        query = 'CREATE TABLE %s (%s)' % (table_name, column_defs)
        response = self.runPostQuery(query)
        # Grab the table id from the response
        table_id = response.split('\n')[1]
    
        return table_id
  
    def createTableFromCSV(self, filename, table_name=None, type_mappings=None):
        """Create a table in Fusion Tables from a CSV file with a header."""
        type_mappings = type_mappings or {}
    
        fin = open(filename)
        csv_reader = csv.reader(fin,delimiter=' ')
        cols = next(csv_reader)
        columns_and_types = [(c, type_mappings.get(c, 'STRING')) for c in cols]
    
        table_id = self.createTable(table_name or filename, columns_and_types)
    
        return table_id
  
    def uploadCSV(self, table_id, filename, bulk=True):
        """Upload a CSV to an existing table."""
        fin = open(filename)
        csv_reader = csv.reader(fin,delimiter=' ')
        header_parts = next(csv_reader)
        col_keys = ','.join(["'%s'" % s for s in header_parts])
        start_time = time.time()
    
        if bulk:
            # Upload multiple rows at once
            max_per_batch = 500
            num_in_batch = max_per_batch
            while num_in_batch == max_per_batch:
                num_in_batch = 0
                queries = []
                for line_parts in csv_reader:
                    line_parts = [s.replace("'", "''") for s in line_parts]
                    fixed_line = ','.join(["'%s'" % s for s in line_parts])
                    query = 'INSERT INTO %s (%s) VALUES (%s)' % (
                        table_id, col_keys, fixed_line)
                    queries.append(query)
                    num_in_batch += 1
                    if num_in_batch == max_per_batch:
                        break
        
                try:
                    full_query = ';'.join(queries)
                    self.runPostQuery(full_query)
                except urllib.error.HTTPError:
                    # Had an error with all the INSERTS; do them one at a time
                    print('Exception hit, subdividing:')
                    for query in queries:
                        try:
                            self.runPostQuery(query)
                        except urllib.error.HTTPError as e2:
                            print('Error at query %s:' % query)
                            print(e2)
          
                    print('Appended %d rows' % num_in_batch)
      
        else:
            # Upload one line at a time
            for line_parts in csv_reader:
                line_parts = [s.strip("'") for s in line_parts]
                fixed_line = ','.join(["'%s'" % s for s in line_parts])
                query = 'INSERT INTO %s (%s) VALUES (%s)' % (
                    table_id, col_keys, fixed_line)
                self.runPostQuery(query)
        end_time = time.time()
        print('Time for upload to %s: %f  (bulk: %s)' % (
            table_id, end_time - start_time, str(bulk)))
  

#
# ClientLogin stuff
#
# This should probably be replaced with the real GData API at some point,
# but now for convenience these functions are included here
#

def GoogleClientLogin(username, pw):
    """Log in to google accounts and return the authorization token."""
    # we use a cookie to authenticate with Google App Engine
    #  by registering a cookie handler here, this will automatically store the
    #  cookie returned when we use urllib2
    cookiejar = http.cookiejar.LWPCookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))
    urllib.request.install_opener(opener)
	
    #
    # get an AuthToken from Google accounts
    #
    auth_uri = 'https://www.google.com/accounts/ClientLogin'
    authreq_data = urllib.parse.urlencode({
        'Email': username,
        'Passwd': pw,
        'service': 'fusiontables',
        'accountType': 'HOSTED_OR_GOOGLE'})
    auth_req = urllib.request.Request(auth_uri, data=authreq_data)
    auth_resp = urllib.request.urlopen(auth_req)
    auth_resp_body = auth_resp.read()
    # auth response includes several fields - we're interested in
    #  the bit after Auth=
    auth_resp_dict = dict(
        x.split('=') for x in auth_resp_body.split('\n') if x)
    authtoken = auth_resp_dict['Auth']
    return authtoken


def GetAuthToken(users_email_address=None, users_password=None):
    """Tries to log in and returns auth token. Saves token for future use.
    
    Will prompt for password if not present.
    """
    # Check to see if it's on disk
    if (os.path.exists('.ftclient_authtoken')):
        token = open('.ftclient_authtoken').read().strip()
    else:
        if not users_email_address:
            users_email_address = input('Email address:')
        if not users_password:
            users_password = getpass.getpass(
                'Password for %s: ' % users_email_address)
    
        token = GoogleClientLogin(users_email_address, users_password)
        
        fout = open('.ftclient_authtoken', 'w')
        fout.write(token)
        fout.close()
  
    return token

if __name__ == '__main__':
    pass
