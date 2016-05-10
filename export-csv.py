#!/usr/bin/python3
#
# Program for exporting patient records from PhenoTips in CSV format
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

optlist, args = getopt(sys.argv[1:], '-y', ['base-url=', 'username=', 'password=', 'study='])
for name, value in optlist:
    if name == '--base-url':
        base_url = value
    elif name == '--username':
        username = value
    elif name == '--password':
        password = value
    elif name == '--study':
        study = value

#get any missing arguments

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

if study == None:
    sys.stderr.write('Are you exporting from a particular study (blank for no)? ')
    study = input()
    if study and study[0] == 'y':
        sys.stderr.write('Input the study to export from (blank for default): ')
        study = input()
    else:
        study = None
elif study == 'None':
    study = None

#begin export

start_time = time.time()
count = 0

bot = PhenoTipsBot(base_url, username, password)
patient_ids = bot.list()
prop_names = bot.list_patient_class_properties()

stderr.write('Looking through ' + str(len(patient_ids)) + ' patient records...\n')

writer = csv.writer(sys.stdout)
writer.writerow(prop_names)

for patient_id in patient_ids:
    stderr.write(str(count) + '\r')
    count += 1

    if study != None:
        patient_study = bot.get_study(patient_id)
        if patient_study != study and not (study == '' and patient_study == None):
            continue

    patient = bot.get(patient_id)
    patient['identifier'] = 'P' + patient['identifier'].zfill(7)
    row = []
    for prop_name in prop_names:
        row.append(patient[prop_name])
    writer.writerow(row)

sys.stderr.write('\n')
sys.stderr.write('All done! Elapsed time ' + str(timedelta(seconds=time.time() - start_time)) + '\n')
