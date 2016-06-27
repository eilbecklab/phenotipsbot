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
    'date_of_death_entered'                : 'String',
    'date_of_birth_entered'                : 'String',
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
    'case_or_control'                      : 'Static List',
    #IBD
    'age_at_diagnosis'                     : 'Float',
    'age_at_enrollment'                    : 'Float',
    'lymphoblast_transformation_date'      : 'Date',
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

def parse_csv_file(file_name, unrecognized_column_callback, unrecognized_value_callback):
    reader = csv.reader(open(file_name, 'r'))
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
                    unrecognized_column_callback(cell)
                j += 1
            continue

        #skip empty rows
        if len(row) == 0:
            continue

        patient = dict()

        for field in column_map:
            value = row[column_map[field]]
            if not value == '':
                patient[field] = normalize(field, value)
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

def import_patients(bot, patients, patient_ids, study, progress_callback):
    count = 0
    start_time = time.time()

    for patient in patients:
        if patient_ids.get(patient.get('external_id')):
            bot.set(patient_ids[patient['external_id']], patient)
        else:
            bot.create(patient, study)
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
    patients = parse_csv_file(
        args[0],
        lambda column: print('WARNING: Ignoring unrecognized column "' + column + '"'),
        lambda value, field: print('WARNING: Ignoring unrecognized value "' + value + '" for "' + field + '"')
    )

    #get any missing arguments and initialize the bot

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

    if study == None:
        studies = bot.list_studies()
        if len(studies):
            print('Available study forms:')
            print('* ' + '\n* '.join(studies))
            study = input('Input the study form to use (blank for default): ')
    elif study == 'None':
        study = None

    #check external IDs

    print('Checking ' + str(len(patients)) + ' external IDs...')

    patient_ids = get_patient_ids(bot, patients, lambda count: stdout.write(str(count) + '\r'))

    #begin import

    n_to_import = str(len(patients) - len(patient_ids))
    n_to_update = str(len(patient_ids))

    if yes or input('You are about to import ' + n_to_import + ' new patients and update ' + n_to_update + ' existing patients. Type y to continue: ')[0] == 'y':
        elapsed_time = import_patients(bot, patients, patient_ids, study, lambda count: stdout.write(str(count) + '\r'))
        print('All done! Elapsed time ' + str(elapsed_time))
