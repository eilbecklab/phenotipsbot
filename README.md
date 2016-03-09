# PhenoTipsBot
**PhenoTipsBot** is a Python framework for manipulating patient data on a
PhenoTips server. Patient records are represented as
[Python dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries),
with each key corresponding to a [PatientClass](https://playground.phenotips.org/bin/PhenoTips/PatientClass)
property and each value being a string. Values are not validated during insertion.

import-csv.py an example program that demonstrates using this framework to
create new patient records from a spreadsheet.

PhenoTipsBot uses a combination of the
[PhenoTips REST API](https://phenotips.org/DevGuide/RESTfulAPI), the
[XWiki REST API](http://platform.xwiki.org/xwiki/bin/view/Features/XWikiRESTfulAPI),
and [PhantomJS](http://phantomjs.org/) because the PhenoTips REST API cannot
manipulate studies, pedigrees, or custom properties that have been added to the
PatientClass. PhenoTips 1.2.2 or later is required.

PhenoTipsBot depends on the
[Python Selenium bindings](https://selenium-python.readthedocs.org/) and the
[Python requests library](http://docs.python-requests.org/en/latest/), but these
can be easily installed with `sudo apt-get install python-selenium` and
`sudo pip install requests`.

## Reference
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
removed from the study name.

#### import_pedigree_ped(patient_id, pedigree_str, mark_evaluated=False, external_id_mark=True, accept_unknown_phenotypes=True)
Replaces the pedigree with one created from the specified
[PED](http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml#ped) string.

#### list()
Returns a list of patient IDs on the server.

#### list_objects(patient_id, object_class)
Returns a list of the numbers of the objects of a particular class that are
attached to the patient page.

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
