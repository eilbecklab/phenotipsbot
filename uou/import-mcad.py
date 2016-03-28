#!/usr/bin/python3
#
# Program for importing patient records from CSV files into PhenoTips
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
import os
import sys
import time
from datetime import timedelta
from getopt import getopt
from getpass import getpass
from sys import stdout

sys.path.append(os.path.dirname(__file__) + '/..')
from phenotipsbot import PhenoTipsBot

#parse arguments

if len(sys.argv) < 2:
    print('Syntax: ./import-mcad [--base-url=<value>] [--username=<value>] [--password=<value>] [--study=<value>] [--yes] <file>')
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

reader = csv.reader(open(args[0], 'r', encoding='utf-16'), delimiter='\t')
patients = []

i = -1
for row in reader:
    i += 1

    #skip first two rows
    if i < 2:
        continue

    patient = {}
    patient['external_id'] = 'mcad:' + row[0]

    clinvar_variants = []
    for column in (4, 8, 12, 16):
        if row[column]:
            clinvar_variant = {}

            clinvar_variant['gene_symbol'] = 'MCAD'
            clinvar_variant['reference_sequence'] = 'NM_000016.4'
            clinvar_variant['hgvs'] = row[column]

            significance_map = {
                'pathogenic': 'Pathogenic',
                'severe pathogenic': 'Pathogenic',
                'pathogenic mild': 'Pathogenic',
                'pathogenic - mild': 'Pathogenic',
                'pathogenic - severe': 'Pathogenic',
                'suspected pathogenic': 'Likely pathogenic',
                'uncertain': 'Uncertain significance',
                'benign': 'Benign',
            }
            significance = row[column + 2].strip().lower()
            if not significance in significance_map:
                raise Exception('Unknown significance "' + row[column + 2] + '"')
            clinvar_variant['clinical_significance'] = significance_map[significance]

            zygosity_map = {
                'homozygous': 'homozygote',
                'heterozygous': 'single heterozygote',
            }
            zygosity = row[column + 3].strip().lower()
            if not zygosity in zygosity_map:
                raise Exception('Unknown zygosity "' + row[column + 3] + '"')
            clinvar_variant['zygosity'] = zygosity_map[zygosity]

            clinvar_variants.append(clinvar_variant)

    phenotype = []
    if int(row[32]) == 1:
        phenotype.append('HP:0001259')
    if int(row[33]) == 1:
        phenotype.append('HP:0001298')
    if int(row[34]) == 1:
        phenotype.append('HP:0002240')
    if int(row[35]) == 1:
        phenotype.append('HP:0001943')
    if int(row[36]) == 1:
        phenotype.append('HP:0001254')
    if int(row[37]) == 1:
        phenotype.append('HP:0001399')
    if int(row[38]) == 1:
        phenotype.append('HP:0006582')
    if int(row[39]) == 1:
        phenotype.append('HP:0001250')
    if int(row[41]) == 1:
        phenotype.append('HP:0002013')
    patient['phenotype'] = '|'.join(phenotype)

    patients.append((patient, clinvar_variants))

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
    for patient, clinvar_variants in patients:
        patient_id = bot.create(patient, study)
        for clinvar_variant in clinvar_variants:
            bot.create_object(patient_id, 'Main.ClinVarVariant', clinvar_variant)
        count += 1
        stdout.write(str(count) + '\r')
    print()
    print('All done! Elapsed time ' + str(timedelta(seconds=time.time() - start_time)))
