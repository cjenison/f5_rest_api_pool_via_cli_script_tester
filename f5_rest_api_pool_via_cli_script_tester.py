#!/usr/bin/python3
# f5_rest_api_pool_via_cli_script_tester.py
# Author: Chad Jenison (c.jenison at f5.com)
# Version 1.1
#
# Script that uses F5 BIG-IP iControl REST API to Add Pools and Virtual Servers after listing all virtuals

import argparse
import sys
import requests
import json
import getpass
import time
from datetime import datetime

requests.packages.urllib3.disable_warnings()

# Taken from http://code.activestate.com/recipes/577058/
def query_yes_no(question, default="no"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

#Setup command line arguments using Python argparse
parser = argparse.ArgumentParser(description='A tool to measure bulk pool adds/removes')
parser.add_argument('--bigip', help='IP or hostname of BIG-IP Management or Self IP', required=True)
parser.add_argument('--user', help='username to use for authentication', required=True)
parser.add_argument('--password', help='password for BIG-IP REST authentication')
parser.add_argument('--poolName', help='BIG-IP Pool Name to Modify', required=True)
parser.add_argument('--members', help='Number of members to add or remove', type=int, default=10)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--add', help='Add Pool Members to Pool', action='store_true')
mode.add_argument('--delete', help='Delete Pool Members to Pool', action='store_true')
parser.add_argument('--poolipprefix', help='IP Prefix for pool members')
parser.add_argument('--interval', type=int, help='Time in seconds to pause between individual pool member changes', default=0) 
restmode = parser.add_mutually_exclusive_group(required=True)
restmode.add_argument('--passthrough', help="When each member change is requested, make iControl REST request", action='store_true')
restmode.add_argument('--defer', help="Defer iControl REST requests until all can be submitted immediately", action='store_true')

args = parser.parse_args()
contentJsonHeader = {'Content-Type': "application/json"}
filename = ''
virtualprefix = 'virtual'
cliScriptName = 'pool-add-remove-members'
## Below two variables are set at extremes to catch best case and worst case execution
restgetbest = 1000
restgetworst = 0
restpostcount = 0
restpostexecutiontime = 0
restdeletecount = 0

scriptbegin = time.time()

def get_auth_token(bigip, username, password):
    authbip = requests.session()
    authbip.verify = False
    payload = {}
    payload['username'] = username
    payload['password'] = password
    payload['loginProviderName'] = 'tmos'
    authurl = 'https://%s/mgmt/shared/authn/login' % (bigip)
    authPost = authbip.post(authurl, headers=contentJsonHeader, data=json.dumps(payload))
    if authPost.status_code == 404:
        print ('attempt to obtain authentication token failed; will fall back to basic authentication; remote LDAP auth will require configuration of local user account')
        token = None
    elif authPost.status_code == 401:
        print ('attempt to obtain authentication token failed due to invalid credentials')
        token = 'Fail'
    elif authPost.json().get('token'):
        token = authPost.json()['token']['token']
        print ('Got Auth Token: %s' % (token))
    else:
        print ('Unexpected error attempting POST to get auth token')
        quit()
    return token

user = args.user
print ('Args.password: %s' % (args.password))
if args.password == '':
    password = getpass.getpass("Password for " + user + ":")
else:
    password = args.password
bip = requests.session()
token = get_auth_token(args.bigip, args.user, password)
if token and token != 'Fail':
    bip.headers.update({'X-F5-Auth-Token': token})
else:
    bip.auth = (args.user, password)
bip.verify = False
requests.packages.urllib3.disable_warnings()
url_base = ('https://%s/mgmt/tm' % (args.bigip))

if args.passthrough:
    transactionDict = {}
    transaction = bip.post('%s/transaction' % (url_base), headers=contentJsonHeader, data=json.dumps(transactionDict)).json()
    transactionId = str(transaction['transId'])
    print ('Transaction ID: %s' % (transactionId))
    transactionPostHeaders = contentJsonHeader.copy()
    transactionPostHeaders['X-F5-REST-Coordination-Id'] = transactionId

for member in range(1, args.members + 1):
    print("Loop variable: %s" % member)
    print ("Sleeping for %s seconds" % (args.interval))
    time.sleep(args.interval)
    if args.passthrough:
        print ('We are in passthrough mode')
        poolMemberDict = { 'name': '%s.%s:80' % (args.poolipprefix, member)}
        poolmemberadd = bip.post('%s/ltm/pool/%s/members' % (url_base, args.poolName), headers=transactionPostHeaders, data=json.dumps(poolMemberDict)).json()

if args.defer:
    transactionDict = {}
    transaction = bip.post('%s/transaction' % (url_base), headers=contentJsonHeader, data=json.dumps(transactionDict)).json()
    transactionId = str(transaction['transId'])
    print ('Transaction ID: %s' % (transactionId))
    transactionPostHeaders = contentJsonHeader.copy()
    transactionPostHeaders['X-F5-REST-Coordination-Id'] = transactionId
    for member in range(1, args.members + 1):
        print("Loop variable: %s" % member)
        poolMemberDict = { 'name': '%s.%s:80' % (args.poolipprefix, member)}
        poolmemberadd = bip.post('%s/ltm/pool/%s/members' % (url_base, args.poolName), headers=transactionPostHeaders, data=json.dumps(poolMemberDict)).json()


## Submit the transaction
submitTransactionPayload = {}
submitTransactionPayload['state'] = "VALIDATING"
print ("Submit Transaction Payload: %s" % (submitTransactionPayload))
submitTransaction = bip.patch('%s/transaction/%s' % (url_base, transactionId), headers=contentJsonHeader, data=json.dumps(submitTransactionPayload)).json()
print ("SubmitTransaction: %s" % submitTransaction)



scriptend = time.time()
scriptruntime = scriptend - scriptbegin