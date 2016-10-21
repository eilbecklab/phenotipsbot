#!/usr/bin/env python3
#
# Program for exporting patient records from PhenoTips into ClinVar CSV
# submission spreadsheets
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
from collections import OrderedDict
from datetime import date
from datetime import timedelta
from dateutil.parser import parse as parsedate
from getopt import getopt
from getpass import getpass
from phenotipsbot import PhenoTipsBot
from sys import stdout

def get_clinvar_data(bot, patient_ids, study, owner, gene, progress_callback):
    start_time = time.time()
    count = 0

    clinvar_data = OrderedDict()

    for patient_id in patient_ids:
        count += 1
        progress_callback(count)

        if study != None:
            patient_study = bot.get_study(patient_id)
            if study != patient_study.lower() and not (study == '' and patient_study == None):
                continue

        if owner:
            patient_owner = bot.get_owner(patient_id)
            if PhenoTipsBot.qualify(patient_owner) != PhenoTipsBot.qualify(owner):
                continue

        clinvar_variant_nums = bot.list_objects(patient_id, 'PhenoTips.ClinVarVariantClass')
        if len(clinvar_variant_nums) == 0:
            continue

        patient_obj = bot.get(patient_id)

        for clinvar_variant_num in clinvar_variant_nums:
            clinvar_variant_obj = bot.get_object(patient_id, 'PhenoTips.ClinVarVariantClass', clinvar_variant_num)
            gene_symbol = clinvar_variant_obj.get('gene_symbol')

            if gene and (not gene_symbol or not gene in gene_symbol.upper().split(';')):
                continue

            #we aggregate all fields except for these
            clinvar_data_key = (
                clinvar_variant_obj['reference_sequence']    if 'reference_sequence'    in clinvar_variant_obj else None,
                clinvar_variant_obj['hgvs']                  if 'hgvs'                  in clinvar_variant_obj else None,
                clinvar_variant_obj['cis_or_trans']          if 'cis_or_trans'          in clinvar_variant_obj else None,
                clinvar_variant_obj['location']              if 'location'              in clinvar_variant_obj else None,
                patient_obj['omim_id']                       if 'omim_id'               in patient_obj         else None,
                clinvar_variant_obj['condition_category']    if 'condition_category'    in clinvar_variant_obj else None,
                clinvar_variant_obj['clinical_significance'] if 'clinical_significance' in clinvar_variant_obj else None,
                clinvar_variant_obj['collection_method']     if 'collection_method'     in clinvar_variant_obj else None,
                clinvar_variant_obj['allele_origin']         if 'allele_origin'         in clinvar_variant_obj else None,
                clinvar_variant_obj['tissue']                if 'tissue'                in clinvar_variant_obj else None,
                patient_obj        ['case_or_control']       if 'case_or_control'       in patient_obj         else None,
            )

            if not clinvar_data_key in clinvar_data:
                clinvar_data[clinvar_data_key] = []

            clinvar_data[clinvar_data_key].append((patient_obj, clinvar_variant_obj))

    return clinvar_data, timedelta(seconds=time.time() - start_time)

def write_clinvar_files(clinvar_data, variant_file, case_data_file):
    start_time = time.time()

    linking_id = 0
    case_count = 0
    max_methods = 0

    aggregate_data = []
    case_data = []

    for clinvar_data_key, clinvar_data_values in clinvar_data.items():
        linking_id += 1
        gene_symbols             = set()
        reference_sequence       = clinvar_data_key[0]
        hgvs                     = clinvar_data_key[1]
        cis_or_trans             = clinvar_data_key[2]
        variation_identifiers    = set()
        location                 = clinvar_data_key[3]
        alternate_designations   = set()
        official_allele_name     = ''
        url                      = ''
        if clinvar_data_key[4]:
            omim_ids             = clinvar_data_key[4].replace('|', ';')
        else:
            omim_ids             = ''
        condition_category       = clinvar_data_key[5]
        clinical_significance    = clinvar_data_key[6]
        date_last_evaluated      = date.min
        mode_of_inheritance      = set()
        collection_method        = clinvar_data_key[7]
        allele_origin            = clinvar_data_key[8]
        clinical_features        = set()
        tissue                   = clinvar_data_key[9]
        if clinvar_data_key[10] == 'case':
            affected_status      = 'yes'
        elif clinvar_data_key[10] == 'control':
            affected_status      = 'no'
        else:
            affected_status      = 'unknown'
        individuals_with_variant = 0
        chromosomes_with_variant = 0
        mosaicism                = 0
        homozygotes              = 0
        single_heterozygotes     = 0
        compound_heterozygotes   = 0
        hemizygotes              = 0
        methods                  = set()

        for patient_obj, clinvar_variant_obj in clinvar_data_values:
            patient_external_id = ''
            patient_clinical_features = []
            patient_sex = ''
            patient_cosanguinity = ''
            patient_condition_comment = ''
            patient_is_proband = ''
            patient_kindred_id = ''
            patient_mosaicism = ''
            patient_zygosity = ''
            variant_method = ('', '')

            if patient_obj.get('external_id'):
                patient_external_id = patient_obj['external_id']
            if clinvar_variant_obj.get('gene_symbol'):
                gene_symbols |= set(clinvar_variant_obj['gene_symbol'].split(';'))
            if clinvar_variant_obj.get('variation_identifiers'):
                variation_identifiers |= set(clinvar_variant_obj['variation_identifiers'].split(';'))
            if clinvar_variant_obj.get('alternate_designations'):
                alternate_designations |= set(clinvar_variant_obj['alternate_designations'].split('|'))
            if clinvar_variant_obj.get('official_allele_name') and not official_allele_name:
                official_allele_name = clinvar_variant_obj['official_allele_name']
            if clinvar_variant_obj.get('url') and not url:
                url = clinvar_variant_obj['url']
            try:
                variant_date_last_evaluated = parsedate(clinvar_variant_obj['date_last_evaluated']).date()
                if variant_date_last_evaluated > date_last_evaluated:
                    date_last_evaluated = variant_date_last_evaluated
            except Exception:
                pass
            if patient_obj.get('global_mode_of_inheritance'):
                for term in patient_obj['global_mode_of_inheritance']:
                    if term == 'HP:0003745':
                        mode_of_inheritance |= 'Sporadic'
                    elif term == 'HP:0000006':
                        mode_of_inheritance |= 'Autosomal dominant inheritance'
                    elif term == 'HP:0001470':
                        mode_of_inheritance |= 'Sex-limited autosomal dominant'
                    elif term == 'HP:0001475':
                        mode_of_inheritance |= 'Male-limited autosomal dominant'
                    elif term == 'HP:0001444':
                        mode_of_inheritance |= 'Autosomal dominant somatic cell mutation'
                    elif term == 'HP:0001452':
                        mode_of_inheritance |= 'Autosomal dominant contiguous gene syndrome'
                    elif term == 'HP:0000007':
                        mode_of_inheritance |= 'Autosomal recessive inheritance'
                    elif term == 'HP:0010985':
                        mode_of_inheritance |= 'Gonosomal inheritance'
                    elif term == 'HP:0001417':
                        mode_of_inheritance |= 'X-linked inheritance'
                    elif term == 'HP:0001423':
                        mode_of_inheritance |= 'X-linked dominant inheritance'
                    elif term == 'HP:0001419':
                        mode_of_inheritance |= 'X-linked recessive inheritance'
                    elif term == 'HP:0001450':
                        mode_of_inheritance |= 'Y-linked inheritance'
                    elif term == 'HP:0001426':
                        mode_of_inheritance |= 'Multifactorial inheritance'
                    elif term == 'HP:0010984':
                        mode_of_inheritance |= 'Digenic inheritance'
                    elif term == 'HP:0010983':
                        mode_of_inheritance |= 'Oligogenic inheritance'
                    elif term == 'HP:0010982':
                        mode_of_inheritance |= 'Polygenic inheritance'
                    elif term == 'HP:0001427':
                        mode_of_inheritance |= 'Mitochondrial inheritance'
            if patient_obj.get('phenotype'):
                patient_clinical_features = set(patient_obj['phenotype'].split('|'))
                clinical_features |= patient_clinical_features
            if patient_obj.get('gender'):
                patient_sex = patient_obj['gender']
            if clinvar_variant_obj.get('mosaicism') == 'yes':
                mosaicism += 1
                patient_mosaicism = 'yes'
            elif clinvar_variant_obj.get('mosaicism') == 'no':
                patient_mosaicism = 'no'
            patient_zygosity = clinvar_variant_obj.get('zygosity')
            if patient_zygosity == 'single heterozygote':
                individuals_with_variant += 1
                chromosomes_with_variant += 1
                single_heterozygotes += 1
            elif patient_zygosity == 'compound heterozygote':
                individuals_with_variant += 1
                chromosomes_with_variant += 1
                compound_heterozygotes += 1
            elif patient_zygosity == 'homozygote':
                individuals_with_variant += 1
                chromosomes_with_variant += 2
                homozygotes += 1
            elif patient_zygosity == 'hemizygote':
                individuals_with_variant += 1
                chromosomes_with_variant += 1
                hemizygotes += 1
            if patient_obj.get('consanguinity') == 0:
                patient_consanguinity = 'no'
            elif patient_obj.get('consanguinity') == 1:
                patient_cosanguinity = 'yes'
            if patient_obj.get('diagnosis_notes'):
                patient_condition_comment = patient_obj['diagnosis_notes']
            if patient_obj.get('subject_data_relationship'):
                if patient_obj['subject_data_relationship'].lower() == 'proband':
                    patient_is_proband = 'yes'
                else:
                    patient_is_proband = 'no'
            if patient_obj.get('kindred_id'):
                patient_kindred_id = patient_obj['kindred_id']
            if clinvar_variant_obj.get('test_name_or_type') or clinvar_variant_obj.get('platform_type'):
                variant_method = (clinvar_variant_obj.get('test_name_or_type', ''), clinvar_variant_obj.get('platform_type', ''))
                methods.add(variant_method)

            case_data.append([
                linking_id,
                patient_external_id,
                collection_method,
                allele_origin,
                affected_status,
                '',
                ';'.join(sorted(patient_clinical_features)),
                tissue,
                patient_sex,
                '',
                '',
                '',
                '',
                patient_cosanguinity,
                patient_condition_comment,
                '',
                patient_is_proband,
                patient_kindred_id,
                '',
                '',
                patient_mosaicism,
                patient_zygosity,
                '',
                '',
                '',
                '',
                '',
                '',
                variant_method[0],
                variant_method[1],
            ])

            case_count += 1

        row = [
            '',
            linking_id,
            ';'.join(sorted(gene_symbols)),
            reference_sequence,
            hgvs,
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            cis_or_trans,
            ';'.join(sorted(variation_identifiers)),
            location,
            '|'.join(sorted(alternate_designations)),
            official_allele_name,
            url,
            '',
            'OMIM',
            omim_ids,
            '',
            condition_category,
            '',
            '',
            clinical_significance,
            date_last_evaluated.isoformat(),
            '',
            '',
            ';'.join(sorted(mode_of_inheritance)),
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            collection_method,
            allele_origin,
            affected_status,
            '',
            ';'.join(sorted(clinical_features)),
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            len(clinvar_data_values),
            '',
            '',
            individuals_with_variant,
            chromosomes_with_variant,
            '',
            '',
            mosaicism,
            homozygotes,
            single_heterozygotes,
            compound_heterozygotes,
            hemizygotes,
            '',
            '',
            '',
            '',
        ]

        for test_name_or_type, platform_type in sorted(methods):
            row.append(test_name_or_type)
            row.append(platform_type)
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')
            row.append('')

        aggregate_data.append(row);

        if len(methods) > max_methods:
            max_methods = len(methods)

    aggregate_columns = [
        '##Local ID',
        'Linking ID',
        'Gene symbol',
        'Reference sequence',
        'HGVS',
        'Chromosome',
        'Start',
        'Stop',
        'Reference allele',
        'Alternate allele',
        'Variant type',
        'Outer start',
        'Inner start',
        'Inner stop',
        'Outer stop',
        'Variant length',
        'Copy number',
        'Reference copy number',
        'Breakpoint 1',
        'Breakpoint 2',
        'Trace or probe data',
        '',
        'Cis or trans',
        'Variation identifiers',
        'Location',
        'Alternate designations',
        'Official allele name',
        'URL',
        '',
        'Condition ID type',
        'Condition ID value',
        'Preferred condition name',
        'Condition category',
        'Condition uncertainty',
        'Condition comment',
        'Clinical significance',
        'Date last evaluated',
        'Assertion method',
        'Assertion method citation',
        'Mode of inheritance',
        'Clinical significance citations',
        'Citations or URLs for clinical significance without database identifiers',
        'Comment on clinical significance',
        'Explanation if clinical significance is other or drug response',
        'Drug response condition',
        'Functional consequence',
        'Comment on functional consequence',
        '',
        'Collection method',
        'Allele origin',
        'Affected status',
        'Structural variant method/analysis type',
        'Clinical features',
        'Tissue',
        'Sex',
        'Age range',
        'Population Group/Ethnicity',
        'Geographic origin',
        'Family history',
        'Indication',
        'Total number of individuals tested',
        'Number of families tested',
        '',
        'Number of individuals with variant',
        'Number of chromosomes with variant',
        'Number of families with variant',
        'Number of families with segregation observed',
        'Mosaicism',
        'Number of homozygotes',
        'Number of single heterozygotes',
        'Number of compound heterozygotes',
        'Number of hemizygotes',
        'Evidence citations',
        'Citations or URLs that cannot be represented in evidence citations column',
        'Comment on evidence',
        '',
        'Test name or type',
        'Platform type',
        'Platform name',
        'Method',
        'Method purpose',
        'Method citations',
        'Software name and version',
        'Software purpose',
        'Testing laboratory',
        'Date variant was reported to submitter',
        '',
        'Comment',
        'Private comment',
        'ClinVarAccession',
        'Novel or Update',
        'Replaces ClinVarAccessions',
    ]

    for i in range(1, max_methods):
        aggregate_columns.insert(76, 'Test name or type')
        aggregate_columns.insert(77, 'Platform type')
        aggregate_columns.insert(78, 'Platform name')
        aggregate_columns.insert(79, 'Method')
        aggregate_columns.insert(80, 'Method purpose')
        aggregate_columns.insert(81, 'Method citations')
        aggregate_columns.insert(82, 'Software name and version')
        aggregate_columns.insert(83, 'Software purpose')
        aggregate_columns.insert(84, 'Testing laboratory')
        aggregate_columns.insert(85, 'Date variant was reported to submitter')

    aggregate_data.insert(0, aggregate_columns)

    case_data.insert(0, [
        '##Linking ID',
        'Individual ID',
        'Collection method',
        'Allele origin',
        'Affected status',
        'Structural variant method/analysis type',
        'Clinical features',
        'Tissue',
        'Sex',
        'Age',
        'Population Group/Ethnicity',
        'Geographic origin',
        'Indication',
        'Family history',
        'Condition comment',
        '',
        'Proband',
        'Family ID',
        'Segregation observed',
        'Secondary finding',
        'Mosaicism',
        'Zygosity',
        'Co-occurrences, same gene',
        'Co-occurrences, other genes',
        'Evidence citations',
        'Citations or URLs that cannot be represented in evidence citations column',
        'Comment on evidence',
        '',
        'Test name or type',
        'Platform type',
        'Platform name',
        'Method',
        'Method purpose',
        'Method citations',
        'Software name and version',
        'Software purpose',
    ])

    csv.writer(variant_file).writerows(aggregate_data)
    csv.writer(case_data_file).writerows(case_data)

    return linking_id, case_count, timedelta(seconds=time.time() - start_time)

if __name__ == '__main__':

    #parse arguments

    base_url = None
    username = None
    password = None
    study = None
    owner = None
    gene = None

    optlist, args = getopt(sys.argv[1:], '', ['base-url=', 'username=', 'password=', 'study=', 'owner=', 'gene='])
    for name, value in optlist:
        if name == '--base-url':
            base_url = value
        elif name == '--username':
            username = value
        elif name == '--password':
            password = value
        elif name == '--gene':
            gene = value.upper()
        elif name == '--study':
            study = value.lower()
        elif name == '--owner':
            owner = value.lower()

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

    if study == None and len(bot.list_studies()):
        study = input('Are you submitting on a particular study (blank for no)? ')
        if study and study[0] == 'y':
            study = input('Input the study to submit on (blank for default): ').lower()
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

    if gene == None:
        gene = input('Input the gene to submit on (blank for all genes): ').upper()

    #begin export

    patient_ids = bot.list()

    print('Looking through ' + str(len(patient_ids)) + ' patient records...')

    clinvar_data, elapsed_time1 = get_clinvar_data(
        bot, patient_ids, study, owner, gene,
        lambda count: stdout.write(count + '\r')
    )

    print('Writing files Variant.csv and CaseData.csv...')

    n_variants, n_cases, elapsed_time2 = write_clinvar_files(
        clinvar_data,
        open('Variant.csv', 'w'),
        open('CaseData.csv', 'w')
    )

    print('Exported ' + str(n_variants) + ' variants and ' + str(n_cases) + ' cases.')
    print('Elapsed time ' + str(elapsed_time1 + elapsed_time2))
