#!/usr/bin/env python3
#
# Program for importing pedigree data from PED files into PhenoTips
#
# Copyright 2016 University of Utah
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import csv
import sys
import time
from datetime import timedelta
from getopt import getopt
from getpass import getpass
from phenotipsbot import PhenoTipsBot
from requests.exceptions import HTTPError
from sys import stdout

#parse arguments

if len(sys.argv) < 2:
    print('You must specify the file to import on the command line.')
    exit(1)

base_url = None
username = None
password = None
yes = False

optlist, args = getopt(sys.argv[1:], '-y', ['base-url=', 'username=', 'password=', 'yes'])
for name, value in optlist:
    if name == '--base-url':
        base_url = value
    elif name == '--username':
        username = value
    elif name == '--password':
        password = value
    elif name in ('-y', '--yes'):
        yes = True

#get any missing arguments

if not base_url:
    base_url = input('Input the URL (blank for http://localhost:8080): ')
if not base_url:
    base_url = 'http://localhost:8080'
if not base_url.startswith('http://') and not base_url.startswith('https://'):
    base_url = 'http://' + base_url
base_url = base_url.rstrip('/')

if not username:
    username = input('Input your username (blank for Admin): ')
if not username:
    username = 'Admin'

if not password:
    password = getpass('Input your password (blank for admin): ')
if not password:
    password = 'admin'

#log in

bot = PhenoTipsBot(base_url, username, password)

#parse PED file
#http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#ped

def get_id(external_id):
    if external_id == '0':
        return None
    try:
        return bot.get_id(external_id)
    except HTTPError:
        return None

print('Matching pedigree rows to the patient database...')
count = 0

reader = csv.reader(open(args[0], 'r'), delimiter='\t')
relatives = list()

for row in reader:
    if len(row) == 0 or row[0][0] == '#':
        continue

    child_external_id = row[1]
    father_external_id = row[2]
    mother_external_id = row[3]

    child_patient_id = get_id(child_external_id)
    father_patient_id = get_id(father_external_id)
    mother_patient_id = get_id(mother_external_id)

    if child_patient_id:
        if father_external_id != '0':
            if not father_patient_id:
                print('WARNING: Adding unknown father ' + father_external_id + ' to ' + child_patient_id)
            relatives.append((child_patient_id, {
                'relative_of': father_external_id,
                'relative_type': 'child',
            }))
        if mother_external_id != '0':
            if not mother_patient_id:
                print('WARNING: Adding unknown mother ' + mother_external_id + ' to ' + child_patient_id)
            relatives.append((child_patient_id, {
                'relative_of': mother_external_id,
                'relative_type': 'child'
            }))
    else:
        print('WARNING: Skipping unknown child ' + child_external_id)

    if father_external_id != '0':
        if father_patient_id:
            if not child_patient_id:
                print('WARNING: Adding unknown child ' + child_external_id + ' to ' + father_patient_id)
            relatives.append((father_patient_id, {
                'relative_of': child_external_id,
                'relative_type': 'parent',
            }))
        else:
            print('WARNING: Skipping unknown father ' + father_external_id)

    if mother_external_id != '0':
        if mother_patient_id:
            if not child_patient_id:
                print('WARNING: Adding unknown child ' + child_external_id + ' to ' + mother_patient_id)
            relatives.append((mother_patient_id, {
                'relative_of': child_external_id,
                'relative_type': 'parent',
            }))
        else:
            print('WARNING: Skipping unknown mother ' + mother_external_id)

    count += 1
    stdout.write(str(count) + '\r')

#begin import

if yes or input('You are about to import ' + str(len(relatives)) + ' relationships. Type y to continue: ')[0] == 'y':
    count = 0
    start_time = time.time()
    for relative in relatives:
        bot.create_relative(relative[0], relative[1])
        count += 1
        stdout.write(str(count) + '\r')
    print('All done! Elapsed time ' + str(timedelta(seconds=time.time() - start_time)))
