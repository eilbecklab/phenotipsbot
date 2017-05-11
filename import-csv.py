#!/usr/bin/env python3
#
# Program for importing patient records from CSV files into PhenoTips
#
# Copyright 2015 University of Utah
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
import re
import sys
import time
from datetime import timedelta
from dateutil.parser import parse as parsedate
from getopt import getopt
from getpass import getpass
from phenotipsbot import PhenoTipsBot
from sys import stdout
from traceback import print_exc

def normalize(field_name, field_value, field_metadata):
    field_value = field_value.strip()
    field_type = field_metadata['type']
    try:
        if field_type == 'Date':
            return parsedate(field_value).strftime('%Y-%m-%d')
        elif field_type == 'Boolean':
            field_value = field_value.lower()
            if field_value in ('t', 'true', 'y', 'yes', '1'):
                return '1'
            elif field_value in ('f', 'false', 'n', 'no', '0'):
                return '0'
            else:
                return None
        elif field_type == 'Number':
            if field_metadata['numberType'] in ('integer', 'long'):
                return int(field_value)
            else:
                return float(field_value)
        elif field_type == 'StaticList':
            possible_values = field_metadata['values']
            if not possible_values:
                return field_value
            field_value = field_value.lower()
            for key, value in possible_values.items():
                if field_value == key.lower() or field_value == value.lower():
                    return key
            return None
        else:
            validationRegex = field_metadata['validationRegExp']
            if validationRegex and not re.fullmatch(validationRegex, field_value):
                return None
            return field_value
    except ValueError:
        return None

def parse_csv_file(bot, file_name, unrecognized_column_callback, unrecognized_value_callback,
                   identifier_column_callback):
    possible_fields = bot.list_patient_class_properties()

    reader = csv.DictReader(open(file_name, 'r'))
    patients = []

    #warn about unrecognized fields
    for field in reader.fieldnames:
        if field == 'identifier':
            identifier_column_callback()
        if field not in possible_fields:
            unrecognized_column_callback(field)

    for row in reader:
        #skip empty rows
        if len(row) == 0:
            continue

        patient = {}

        for field in reader.fieldnames:
            if field == 'identifier':
                continue
            value = row[field]
            if value == '':
                continue
            patient[field] = normalize(field, value, possible_fields[field])
            if patient[field] == None:
                del patient[field]
                unrecognized_value_callback(value, field)

        patients.append(patient)

    return patients

def get_patient_ids(bot, patients, progress_callback):
    patient_ids = {}
    count = 0

    for patient in patients:
        external_id = patient.get('external_id')
        if external_id:
            patient_id = bot.get_id(external_id)
            if patient_id:
                patient_ids[external_id] = patient_id
            count += 1
            progress_callback(count)

    return patient_ids

def import_patients(bot, patients, patient_ids, study, owner, progress_callback):
    count = 0
    start_time = time.time()

    for patient in patients:
        if patient_ids.get(patient.get('external_id')):
            bot.set(patient_ids[patient['external_id']], patient)
        else:
            bot.create(patient, study, owner)
        count += 1
        progress_callback(count)

    return timedelta(seconds=time.time() - start_time)

if __name__ == '__main__':

    #parse arguments

    if len(sys.argv) < 2:
        print('You must specify the file to import on the command line.')
        exit(1)

    base_url = None
    username = None
    password = None
    study = None
    owner = None
    yes = False

    optlist, args = getopt(sys.argv[1:], '-y', ['base-url=', 'username=', 'password=', 'study=', 'owner=', 'yes'])
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
        elif name in ('-y', '--yes'):
            yes = True

    #get missing arguments and initialize the bot

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

    bot = PhenoTipsBot(base_url, username, password)

    #parse CSV file

    patients = parse_csv_file(
        bot,
        args[0],
        lambda column: print('WARNING: Ignoring unrecognized column "' + column + '"'),
        lambda value, field: print('WARNING: Ignoring unrecognized value "' + value + '" for "' + field + '"'),
        lambda: print('WARNING: Ignoring identifier column; all existing patients must be identified using the external_id column and all new patients must receive new PhenoTips IDs.')
    )

    #get the rest of the missing arguments

    if study == None:
        studies = bot.list_studies()
        if len(studies):
            print('Available study forms:')
            print('* ' + '\n* '.join(studies))
            study = input('Input the study form to use (blank for default): ')
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
            owner = input('Input which user or group should own (have access to) the new patients (blank for ' + username + '): ')
    if not owner:
        owner = username

    #check external IDs

    print('Checking ' + str(len(patients)) + ' external IDs...')

    patient_ids = get_patient_ids(bot, patients, lambda count: stdout.write(str(count) + '\r'))

    #begin import

    n_to_import = str(len(patients) - len(patient_ids))
    n_to_update = str(len(patient_ids))

    if yes or input('You are about to import ' + n_to_import + ' new patients and update ' + n_to_update + ' existing patients. Type y to continue: ')[0] == 'y':
        elapsed_time = import_patients(bot, patients, patient_ids, study, owner, lambda count: stdout.write(str(count) + '\r'))
        print('All done! Elapsed time ' + str(elapsed_time))
