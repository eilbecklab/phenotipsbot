#!/usr/bin/env python3
#
# Program for exporting patient relationships from PhenoTips in PED format
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
from sys import stderr
from sys import stdout

#parse arguments

base_url = None
username = None
password = None
study = None
owner = None

optlist, args = getopt(sys.argv[1:], '-y', ['base-url=', 'username=', 'password=', 'study=', 'owner='])
for name, value in optlist:
    if name == '--base-url':
        base_url = value
    elif name == '--username':
        username = value
    elif name == '--password':
        password = value
    elif name == '--study':
        study = value
    elif name == '--owner':
        owner = value

#get any missing arguments and initialize the bot

if not base_url:
    sys.stderr.write('Input the URL (blank for http://localhost:8080): ')
    base_url = input()
if not base_url:
    base_url = 'http://localhost:8080'
if not base_url.startswith('http://') and not base_url.startswith('https://'):
    base_url = 'http://' + base_url
base_url = base_url.rstrip('/')

if not username:
    sys.stderr.write('Input your username (blank for Admin): ')
    username = input()
if not username:
    username = 'Admin'

if not password:
    password = getpass('Input your password (blank for admin): ', sys.stderr)
if not password:
    password = 'admin'

bot = PhenoTipsBot(base_url, username, password)

if study == None:
    studies = bot.list_studies()
    if len(studies):
        print('Available studies:')
        print('* ' + '\n* '.join(studies))
        sys.stderr.write('Are you exporting from a particular study (blank for no)? ')
        study = input()
        if study and study[0] == 'y':
            sys.stderr.write('Input the study to export from (blank for default): ')
            study = input()
        else:
            study = None
elif study == 'None':
    study = None

if owner == None:
    users = bot.list_users()
    groups = bot.list_groups()
    if len(users) > 1:
        print('Available users:')
        print('* ' + '\n* '.join(users))
    if len(groups):
        print('Available work groups:')
        print('* ' + '\n* Groups.'.join(groups))
    if len(users) > 1 or len(groups):
        owner = input('Input which user or group\'s patients to export (blank for all users): ')

#begin export

start_time = time.time()
count = 0

patient_ids = bot.list(study, owner)

stderr.write('Looking through ' + str(len(patient_ids)) + ' patient records...\n')
stderr.write('\n')

stdout.write('#FID\tIID\tPAT\tMAT\tSEX\tPHENOTYPE\n')
writer = csv.writer(sys.stdout, delimiter='\t')

fid = study if study else '0'

for patient_id in patient_ids:
    stderr.write(str(count) + '\r')
    count += 1

    patient = bot.get(patient_id)
    iid = patient['external_id']
    pat = '0'
    mat = '0'
    if patient.get('gender') == 'M':
        sex = 1
    elif patient.get('gender') == 'F':
        sex = 2
    else:
        sex = 0
    if patient.get('case_or_control') == 'case':
        phenotype = 2
    elif patient.get('case_or_control') == 'control':
        phenotype = 1
    else:
        phenotype = 0

    for relative_num in bot.list_relatives(patient_id):
        relative_obj = bot.get_relative(patient_id, relative_num)
        relative_eid = relative_obj['relative_of']
        if not relative_eid:
            raise Exception('Relative ' + relative_num + ' of patient ' + patient_id + ' is malformed')
        relative = bot.get(bot.get_id(relative_eid))
        if relative_obj['relative_type'] == 'child':
            if relative['gender'] == 'M':
                if pat != '0':
                    raise Exception('Patient ' + iid + ' has two fathers: ' + pat + ' and ' + relative_eid)
                pat = relative_eid
            elif relative['gender'] == 'F':
                if mat != '0':
                    raise Exception('Patient ' + iid + ' has two mothers: ' + mat + ' and ' + relative_eid)
                mat = relative_eid
            else:
                raise Exception('Parent ' + relative_eid + ' is neither male nor female')

    stderr.write('          \r')
    writer.writerow([fid, iid, pat, mat, sex, phenotype])

stderr.write('\n')
stderr.write('All done! Elapsed time ' + str(timedelta(seconds=time.time() - start_time)) + '\n')
