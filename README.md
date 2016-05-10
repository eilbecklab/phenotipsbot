**PhenoTipsBot** is a Python framework for manipulating patient data on a
[PhenoTips](http://phenotips.org/) website. Patient records are represented as
[Python dictionaries]
(https://docs.python.org/3/tutorial/datastructures.html#dictionaries),
with each key corresponding to a [PatientClass]
(https://playground.phenotips.org/bin/PhenoTips/PatientClass) property and each
value being a string. Values are not validated during insertion.

This repository also includes several sample programs that use the PhenoTipsBot
framework to perform common import and export operations. Use these as examples
to create scripts that meet more complex needs.

PhenoTipsBot depends on the
[Python Selenium bindings](https://selenium-python.readthedocs.org/), the
[Python requests library](http://docs.python-requests.org/en/latest/), and
[PhantomJS](http://phantomjs.org/), but these can be easily installed with
either `sudo apt-get install python-selenium phantomjs` or
`sudo pacman -S python-selenium phantomjs` and `sudo pip install requests`.

PhenoTipsBot uses a combination of the
[PhenoTips REST API](https://phenotips.org/DevGuide/RESTfulAPI), the
[XWiki REST API]
(http://platform.xwiki.org/xwiki/bin/view/Features/XWikiRESTfulAPI), and
[PhantomJS](http://phantomjs.org/) because the PhenoTips REST API cannot
manipulate studies, pedigrees, or custom properties that have been added to the
PatientClass. PhenoTips 1.2.2 or later is required.

## Table of contents
* [Caution](#caution)
* [Sample programs](#sample-programs)
    * [import-csv.py](#import-csvpy)
    * [export-csv.py](#export-csvpy)
    * [import-ped.py](#import-pedpy)
    * [export-ped.py](#export-pedpy)
    * [export-clinvar.py](#export-clinvarpy)
* [Framework reference](#framework-reference)
    * [PhenoTipsBot](#phenotipsbot-1)
    * [ApgarType](#apgartype)
    * [RelativeType](#relativetype)
    * [SexType](#sextype)
* [License](#license)

## Caution
It is a good idea to make a copy of your PhenoTips site and test changes locally
instead of on the production server. To do so:

1. Download and unzip a copy of PhenoTips onto your local machine.
2. Delete the data directory inside the phenotips directory.
3. Copy the data directory from your production copy of PhenoTips into the local
   phenotips directory.
4. Start the local copy of PhenoTips. It will behave exactly like the production
   copy, including using the same usernames and passwords.

## Sample programs
### [import-csv.py](import-csv.py)
#### Synopsis
```
./import-csv [--base-url=<value>] [--username=<value>] [--password=<value>]
             [--study=(<value> | None)] [--update] [-y | --yes] <file>
```

#### Description
Imports new patient records from a spreadsheet.

The first row of the spreadsheet must contain the names of the PhenoTips fields
that correspond to each column. You can see a list of PhenoTips field names by
going to `/bin/PhenoTips/PatientClass` on your PhenoTips site.

#### Options
* `--base-url`
    * The location of the PhenoTips site, for example `http://localhost:8080`.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--username`
    * The username to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--password`
    * The password to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--study`
    * The study form to use when creating new patients. Pass `--study=""` to
      use the default study form. Pass `--study=None` if there are no custom
      study forms, to avoid adding a StudyBindingClass object to the new
      patients.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--update`
    * If this option is specified, values from the spreadsheet correspond to
      existing patients on the PhenoTips site. The spreadsheet must contain an
      external_id column to match patients on the spreadsheet with patients on
      the site.
* `-y, --yes`
    * If this option is specified, the script does not ask for confirmation
      before performing any operations.
* `<file>`
    * The CSV file to import.

#### Example
The file [example.csv](example.csv) contains a single patient to import:

```
diagnosis_notes,enrollment_date,consent_signed_date,subject_mmi,external_id,lab_id,kindred_id,gender,subject_data_relationship,investigator,home_zip_code
Cardio-facio-cutaneous syndrome,12/1/2015,12/1/2015,1234,mmi:1234,12345,6789,Female,Proband,Henrie,84108
```

A few of the columns are custom fields which have been added to the University
of Utah's PhenoTips site. If your PhenoTips site does not support these
properties, they will be ignored.

To import the spreadsheet:

```
$ ./import-csv.py example.csv 
Input the URL (blank for http://localhost:8080): 
Input your username (blank for Admin): 
Input your password (blank for admin): 
Are there any custom study forms (blank for no)? 
You are about to import 3 patients. Type y to continue: y
All done! Elapsed time 0:00:06.643825
```

### [export-csv.py](export-csv.py)
#### Synopsis
```
./export-csv [--base-url=<value>] [--username=<value>] [--password=<value>]
             [--study=(<value> | None)]
```

#### Description
Exports patient records (to the standard output) in CSV format.

#### Options
* `--base-url`
    * The location of the PhenoTips site, for example `http://localhost:8080`.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--username`
    * The username to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--password`
    * The password to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--study`
    * The study to export patients from. Pass `--study=None` to export all
      patients. Pass `--study=""` to export patients from the default study.
    * The script will prompt for this value if it is not provided on the command
      line.

#### Example
To export a spreadsheet:

```
$ ./export-csv.py | tee patients.csv
Input the URL (blank for http://localhost:8080): 
Input your username (blank for Admin): 
Input your password (blank for admin): 
Are you exporting from a particular study (blank for no)? 
Looking through 3 patient records...

identifier,external_id,exam_date,first_name,last_name,date_of_birth,gender,global_age_of_onset,global_mode_of_inheritance,indication_for_referral,health_card,proband,family_of,maternal_ethnicity,paternal_ethnicity,ivf,consanguinity,miscarriages,omim_id,unaffected,phenotype,negative_phenotype,prenatal_phenotype,negative_prenatal_phenotype,prenatal_development,gestation,family_history,pedigree,diagnosis_notes,medical_history,reports_history,extended_phenotype,extended_prenatal_phenotype,extended_negative_phenotype,extended_negative_prenatal_phenotype,apgar1,apgar5,assistedReproduction_fertilityMeds,assistedReproduction_surrogacy,solved,solved__pubmed_id,solved__gene_id,date_of_death,date_of_death_entered,date_of_birth_entered,solved__notes,assistedReproduction_donoregg,date_of_death_unknown,assistedReproduction_donorsperm,icsi,affectedRelatives,multipleGestation,assistedReproduction_iui
P0000001,mmi:1001,,,,,F,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,
P0000002,mmi:1002,,,,,M,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,
P0000003,mmi:1003,,,,,F,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,

All done! Elapsed time 0:00:00.246130
```

After running this command, patients.csv contains:

```
identifier,external_id,exam_date,first_name,last_name,date_of_birth,gender,global_age_of_onset,global_mode_of_inheritance,indication_for_referral,health_card,proband,family_of,maternal_ethnicity,paternal_ethnicity,ivf,consanguinity,miscarriages,omim_id,unaffected,phenotype,negative_phenotype,prenatal_phenotype,negative_prenatal_phenotype,prenatal_development,gestation,family_history,pedigree,diagnosis_notes,medical_history,reports_history,extended_phenotype,extended_prenatal_phenotype,extended_negative_phenotype,extended_negative_prenatal_phenotype,apgar1,apgar5,assistedReproduction_fertilityMeds,assistedReproduction_surrogacy,solved,solved__pubmed_id,solved__gene_id,date_of_death,date_of_death_entered,date_of_birth_entered,solved__notes,assistedReproduction_donoregg,date_of_death_unknown,assistedReproduction_donorsperm,icsi,affectedRelatives,multipleGestation,assistedReproduction_iui
P0000001,mmi:1001,,,,,F,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,
P0000002,mmi:1002,,,,,M,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,
P0000003,mmi:1003,,,,,F,,,,,1,,,,,,,,0,,,,,,,,,Cardio-facio-cutaneous syndrome,,,,,,,unknown,unknown,,,0,,,,,,,,,,,,,
```

### [import-ped.py](import-ped.py)
#### Synopsis
```
./import-ped [--base-url=<value>] [--username=<value>] [--password=<value>]
             [-y | --yes] <file>
```

#### Description
Imports a [PED](http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#ped)
pedigree file as a set of relationships.

This script adds RelativeClass objects to patients that correspond to the lines
in the pedigree file. The IDs in the PED file must correspond to the external
IDs of patients on the PhenoTips site.

#### Options
* `--base-url`
    * The location of the PhenoTips site, for example `http://localhost:8080`.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--username`
    * The username to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--password`
    * The password to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `-y, --yes`
    * If this option is specified, the script does not ask for confirmation
      before performing any operations.
* `<file>`
    * The PED file to import.

#### Example
The file [example.ped](example.ped) contains only one line, but it represents
two child-to-parent and two parent-to-child relationships:

```
#FID	IID	PAT	MAT	SEX	PHENOTYPE
foobar	mmi:1001	mmi:1002	mmi:1003	2	1
```

To import the pedigree:

```
$ ./import-ped.py example.ped 
Input the URL (blank for http://localhost:8080): 
Input your username (blank for Admin): 
Input your password (blank for admin): 
Matching pedigree rows to the patient database...
You are about to import 4 relationships. Type y to continue: y
All done! Elapsed time 0:00:01.418184
```

### [export-ped.py](export-ped.py)
#### Synopsis
```
./export-csv [--base-url=<value>] [--username=<value>] [--password=<value>]
             [--study=(<value> | None)]
```

#### Description
Exports patient relationships (to the standard output) in PED format.

#### Options
* `--base-url`
    * The location of the PhenoTips site, for example `http://localhost:8080`.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--username`
    * The username to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--password`
    * The password to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--study`
    * The study to export patient relationships from. Pass `--study=None` to
      export the relationships of all patients. Pass `--study=""` to export
      relationships of patients from the default study. If a patient has
      relationships to patients outside of the study, the relationships of the
      patients in the study to the patients outside of the study will be
      exported but other relationships of the patients outside of the study will
      not be exported.
    * The script will prompt for this value if it is not provided on the command
      line.

#### Example
To export a pedigree:

```
$ ./export-ped.py | tee pedigree.ped
Input the URL (blank for http://localhost:8080): 
Input your username (blank for Admin): 
Input your password (blank for admin): 
Are you exporting from a particular study (blank for no)? 
Looking through 3 patient records...

#FID	IID	PAT	MAT	SEX	PHENOTYPE
0       mmi:1001	mmi:1002	mmi:1003	2	0
0       mmi:1002	0	0	1	0
0       mmi:1003	0	0	2	0

All done! Elapsed time 0:00:00.392940
```

After running this command, pedigree.ped contains:

```
#FID	IID	PAT	MAT	SEX	PHENOTYPE
0       mmi:1001	mmi:1002	mmi:1003	2	0
0       mmi:1002	0	0	1	0
0       mmi:1003	0	0	2	0
```

### [export-clinvar.py](export-clinvar.py)
#### Synopsis
```
./export-clinvar [--base-url=<value>] [--username=<value>] [--password=<value>]
                 [--study=(<value> | None)]
```

#### Description
Exports variants attached to patients to Variants.csv and CaseData.csv for
[https://www.ncbi.nlm.nih.gov/clinvar/docs/submit/](submission to ClinVar).

This feature will only work if you have set up the ClinVarVariant class and used
it to document specific variants. See [PhenoTips Site Administration]
(https://github.com/eilbecklab/phenotips-docs/blob/master/SiteAdministration.md#clinvar)
for more information.

#### Options
* `--base-url`
    * The location of the PhenoTips site, for example `http://localhost:8080`.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--username`
    * The username to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--password`
    * The password to use to access the PhenoTips site.
    * The script will prompt for this value if it is not provided on the command
      line.
* `--study`
    * The study to export patients from. Pass `--study=None` to export all
      patients. Pass `--study=""` to export patients from the default study.
    * The script will prompt for this value if it is not provided on the command
      line.

#### Example
To export variants:

```
$ ./export-clinvar.py 
Input the URL (blank for http://localhost:8080): 
Input your username (blank for Admin): 
Input your password (blank for admin): 
Input the gene to submit on (blank for all genes): acadm
Are you submitting on a particular study (blank for no)? 
Looking through 1192 patient records...
Writing files Variant.csv and CaseData.csv...
Exported 83 variants and 301 cases.
Elapsed time 0:00:22.582335
```

After running this command, Variant.csv and CaseData.csv contain data
corresponding to the Variant tab and the CaseData tab of the official
[ClinVar full submission spreadsheet]
(ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/submission_templates/SubmissionTemplate.xlsx).
Variant.csv contains aggregate data and CaseData.csv contains case-level data.

## Framework reference
### PhenoTipsBot
#### PhenoTipsBot(base_url, username, password)
Constructs a PhenoTipsBot instance with the specified parameters. The base URL
should include the protocol but no trailing slash. Any changes made to the
server will be logged under the provided username.

#### create(patient_obj, study, pedigree)
Creates a new patient page and returns the patient ID (e.g. 'P000123'). If
patient_obj, study, or pedigree is given, set, set_study, or set_pedigree is
also called.

#### create_object(patient_id, object_class, object_obj)
Creates an arbitrary object on a patient page and returns its object number.

#### create_relative(patient_id, relative_obj)
Creates a new relative relationship and returns the relative number.

#### delete(patient_id)
Deletes a patient page.

#### delete_object(patient_id, object_class, object_num)
Deletes an arbitrary object from a patient page.

#### delete_relative(patient_id, relative_num)
Deletes a relative relationship.

#### export_pedigree_ped(patient_id, id_generation='external')
Returns a string in
[PED](http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#ped) format that
represents the pedigree data. id_generation can be 'external', 'newid', or
'name'.

#### get(patient_id)
Returns a patient object corresponding to the patient with the specified ID.

#### get_id(external_id):
Translates an external ID to a patient ID.

#### get_object(patient_id, object_class, object_num)
Returns an arbitrary object on a patient page.

#### get_pedigree(patient_id)
Returns the patient's pedigree, which is displayed to the user as an SVG image,
as an object deserialized from the internal JSON representation.

#### get_relative(patient_id, relative_num)
Returns the patient's relative with the specified number.

#### get_study(patient_id)
Returns the name of the patient's study form. 'xwiki:Studies.' is automatically
removed from the study name. If the patient does not have a StudyBindingClass
(usually because no studies have been defined), this function returns None. If
the patient does have a StudyBindingClass but it's set to the default study
form, this function returns an empty string.

#### import_pedigree_ped(patient_id, pedigree_str, mark_evaluated=False, external_id_mark=True, accept_unknown_phenotypes=True)
Replaces the pedigree with one created from the specified
[PED](http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#ped) string.

#### list()
Returns a list of patient IDs on the server.

#### list_objects(patient_id, object_class)
Returns a list of the numbers of the objects of a particular class that are
attached to the patient page.

#### list_patient_class_properties()
Returns a list of the possible property names that a patient object can have.

#### list_relatives(patient_id)
Returns a list of the numbers of the relatives attached to the patient page.

#### set(patient_id, patient_obj)
Updates the properties of the patient from the values in the patient object.
Only properties that exist in both the patient object and on the server are
updated.

#### set_object(patient_id, object_class, object_obj)
Updates the properties of an object. Only properties that exist in both
object_obj and on the server are updated.

#### set_pedigree(patient_id, pedigree_obj)
Sets the patient's pedigree data and updates the SVG image that is shown to the
user.

#### set_relative(patient_id, relative_num, relative_obj)
Sets the relative's name and relationship. The relative must already exist.

#### set_study(patient_id, study)
Sets the patient's study form. Pass `study=''` for the default study form, or
`study=None` for the default study form and no study link. 'xwiki:Studies.' is
automatically prepended to the study name.

### ApgarType
* ApgarType.unknown

### RelativeType
* RelativeType.aunt_uncle
* RelativeType.child
* RelativeType.cousin
* RelativeType.grandchild
* RelativeType.grandparent
* RelativeType.niece_nephew
* RelativeType.parent
* RelativeType.sibling
* RelativeType.twin

### SexType
* Sex.male
* Sex.female
* Sex.other

## License
Copyright 2015 University of Utah

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
USA
