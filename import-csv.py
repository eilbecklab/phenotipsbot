#!/usr/bin/python3
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
import sys
import time
from datetime import timedelta
from dateutil.parser import parse as parsedate
from getopt import getopt
from getpass import getpass
from phenotipsbot import PhenoTipsBot
from sys import stdout
from traceback import print_exc

KNOWN_FIELDS = {
    #phenotips
    'external_id'                          : 'String',
    'exam_date'                            : 'Date',
    'first_name'                           : 'String',
    'last_name'                            : 'String',
    'date_of_birth'                        : 'Date',
    'gender'                               : 'Sex',
    'global_age_of_onset'                  : 'Database List',
    'global_mode_of_inheritance'           : 'Database List',
    'indication_for_referral'              : 'String',
    'health_card'                          : 'String',
    'proband'                              : 'Boolean',
    'family_of'                            : 'Database List',
    'maternal_ethnicity'                   : 'Race',
    'paternal_ethnicity'                   : 'Race',
    'ivf'                                  : 'Boolean',
    'consanguinity'                        : 'Boolean',
    'miscarriages'                         : 'Boolean',
    'omim_id'                              : 'Database List',
    'unaffected'                           : 'Boolean',
    'phenotype'                            : 'Database List',
    'negative_phenotype'                   : 'Database List',
    'prenatal_phenotype'                   : 'Database List',
    'negative_prenatal_phenotype'          : 'Database List',
    'prenatal_development'                 : 'String',
    'gestation'                            : 'Integer',
    'family_history'                       : 'String',
    'pedigree'                             : 'Database List',
    'diagnosis_notes'                      : 'String',
    'medical_history'                      : 'String',
    'reports_history'                      : 'Database List',
    'extended_phenotype'                   : 'Database List',
    'extended_prenatal_phenotype'          : 'Database List',
    'extended_negative_phenotype'          : 'Database List',
    'extended_negative_prenatal_phenotype' : 'Database List',
    'apgar1'                               : 'Static List',
    'apgar5'                               : 'Static List',
    'assistedReproduction_fertilityMeds'   : 'Boolean',
    'assistedReproduction_surrogacy'       : 'Boolean',
    'solved'                               : 'Boolean',
    'solved__pubmed_id'                    : 'String',
    'solved__gene_id'                      : 'String',
    'date_of_death'                        : 'Date',
    'solved__notes'                        : 'String',
    'assistedReproduction_donoregg'        : 'Boolean',
    'date_of_death_unknown'                : 'Boolean',
    'assistedReproduction_donorsperm'      : 'Boolean',
    'icsi'                                 : 'Boolean',
    'affectedRelatives'                    : 'Boolean',
    'multipleGestation'                    : 'Boolean',
    'assistedReproduction_iui'             : 'Boolean',
    #phenotype core
    'enrollment_date'                      : 'Date String',
    'consent_signed_date'                  : 'Date String',
    'subject_mmi'                          : 'Integer',
    'lab_id'                               : 'Integer',
    'kindred_id'                           : 'Integer',
    'subject_data_relationship'            : 'String',
    'investigator'                         : 'String',
    'home_zip_code'                        : 'Integer',
    #IBD
    'age_at_diagnosis'                     : 'Float',
    'age_at_enrollment'                    : 'Float',
}

def normalize(field_name, value):
    field_type = KNOWN_FIELDS[field_name]
    try:
        if field_type in ('Date', 'Date String'):
            return parsedate(value).strftime('%Y-%m-%d')
        elif field_type == 'Sex':
            value = value.strip().lower()
            if value in ('m', 'male'):
                return 'M'
            elif value in ('f', 'female'):
                return 'F'
            elif value in ('o', 'other'):
                return 'O'
            else:
                return None
        elif field_type == 'Boolean':
            value = value.strip().lower()
            if value in ('t', 'true', 'y', 'yes', '1'):
                return '1'
            elif value in ('f', 'false', 'n', 'no', '0'):
                return '0'
            else:
                return None
        elif field_type == 'Integer':
            return int(value)
        elif field_type == 'Float':
            return float(value)
        else:
            return value
    except ValueError:
        return None

#parse arguments

if len(sys.argv) < 2:
    print('Syntax: ./import-csv [--base-url=<value>] [--username=<value>] [--password=<value>] [--study=<value>] [--yes] <file>')
    exit(1)

base_url = None
username = None
password = None
study = None
yes = False

optlist, args = getopt(sys.argv[1:], '-y', ['base-url=', 'username=', 'password=', 'study=', 'yes'])
for name, value in optlist:
    if name == '--base-url':
        base_url = value
    elif name == '--username':
        username = value
    elif name == '--password':
        password = value
    elif name == '--study':
        study = value
    elif name in ('-y', '--yes'):
        yes = True

#parse CSV file

reader = csv.reader(open(args[0], 'r'))
column_map = dict()
patients = list()

i = -1
for row in reader:
    i += 1

    #skip first row
    if i == 0:
        j = 0
        for cell in row:
            if cell in KNOWN_FIELDS:
                column_map[cell] = j
            else:
                print('WARNING: Ignoring unrecognized column "' + cell + '"')
            j += 1
        continue

    patient = dict()

    for field in column_map:
        value = row[column_map[field]]
        if not value == '':
            patient[field] = normalize(field, value)
            if patient[field] == None:
                del patient[field]
                print('WARNING: Ignoring unrecognized value "' + value + '" for "' + field + '"')

    patients.append(patient)

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

if study == None:
    study = input('Are there any custom study forms (blank for no)? ')
    if study and study[0] == 'y':
        study = input('Input the study form to use (blank for default): ')
    else:
        study = None

#begin import

if yes or input('You are about to import ' + str(len(patients)) + ' patients. Type y to continue: ')[0] == 'y':
    bot = PhenoTipsBot(base_url, username, password)
    count = 0
    start_time = time.time()
    for patient in patients:
        bot.create(patient, study)
        count += 1
        stdout.write(str(count) + '\r')
    print()
    print('All done! Elapsed time ' + str(timedelta(seconds=time.time() - start_time)))
