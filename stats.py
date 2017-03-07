#!/usr/bin/env python3
#
# Program for getting statistics about a PhenoTips site
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

import sys
from getopt import getopt
from getpass import getpass
from phenotipsbot import PhenoTipsBot
from sys import stderr

#parse arguments

base_url = None
username = None
password = None
wanted_users = []
wanted_studies = []

optlist, args = getopt(sys.argv[1:], '', ['base-url=', 'username=', 'password=', 'of-user=', 'of-study='])
for name, value in optlist:
    if name == '--base-url':
        base_url = value
    elif name == '--username':
        username = value
    elif name == '--password':
        password = value
    elif name == '--of-user':
        wanted_users.append(value.lower())
    elif name == '--of-study':
        wanted_studies.append(value.lower())

#get any missing arguments and initialize the bot

if not base_url:
    sys.stderr.write('Input the URL (blank for http://localhost:8080): ')
    sys.stderr.flush()
    base_url = input()
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

bot = PhenoTipsBot(base_url, username, password)

patient_ids = bot.list()

stderr.write('Looking through ' + str(len(patient_ids)) + ' patient records...\n')
stderr.write('\n')

count = 0
patient_total = 0
positive_phenotype_total = 0
negative_phenotype_total = 0
owners = set()
studies = set()
fields_used = set()
for patient_id in patient_ids:
    stderr.write(str(count) + '\r')
    count += 1

    owner = bot.get_owner(patient_id) or ''
    study = bot.get_study(patient_id) or ''
    if ((len(wanted_users) == 0 or owner.lower() in wanted_users) and
            (len(wanted_studies) == 0 or study.lower() in wanted_studies)):
        patient_total += 1
        owners.add(owner)
        studies.add(study)
        patient = bot.get(patient_id)
        if patient['phenotype']:
            positive_phenotype_total += len(patient['phenotype'].split('|'))
        if patient['negative_phenotype']:
            negative_phenotype_total += len(patient['negative_phenotype'].split('|'))
        for key, value in patient.items():
            if value:
                #print(key + ': ' + value)
                fields_used.add(key)

print('Owned patients: ' + str(patient_total))
print('Average positive phenotypes per patient: ' + str(positive_phenotype_total / patient_total))
print('Average negative phenotypes per patient: ' + str(negative_phenotype_total / patient_total))
print('Owners: ' + str(len(owners)) + ', ' + str(sorted(owners)))
print('Study forms: ' + str(len(studies)) + ', ' + str(sorted(studies)))
print('Fields used at least once: ' + str(len(fields_used)) + ', ' + str(sorted(fields_used)))
