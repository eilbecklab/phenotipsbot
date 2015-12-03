# PhenoTipsBot
# Framework for manipulating patient data on a PhenoTips server
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

import requests
from xml.etree import ElementTree

class PhenoTipsBot:
    def __init__(self, base_url, username, password):
        self.base = base_url
        self.auth = (username, password)

    def create(self, patient_obj=None, study=None):
        r = requests.post(self.base + '/rest/patients', auth=self.auth)
        r.raise_for_status()
        patient_id = r.headers['location']
        patient_id = patient_id[patient_id.rfind('/')+1:]
        if patient_obj:
            self.set(patient_id, patient_obj)
        if study:
            self.set_study(patient_id, study)
        return patient_id

    def delete(self, patient_id):
        r = requests.delete(self.base + '/rest/patients/' + patient_id, auth=self.auth)
        r.raise_for_status()

    def get(self, patient_obj):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.PatientClass/0/properties'
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        root = ElementTree.fromstring(r.text)
        ret = {}
        for prop in root.iter('{http://www.xwiki.org}property'):
            ret[prop.attrib['name']] = prop.find('{http://www.xwiki.org}value').text
        return ret

    def get_study(self, patient_id):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.StudyBindingClass/0'
        r = requests.get(url, auth=self.auth)
        if r.status_code == 404:
            return None
        else:
            r.raise_for_status()
            tree = ElementTree.parse(StringIO(r.text))
            el = tree.find('{http://www.xwiki.org}property[@name="studyReference"]/{http://www.xwiki.org}value')
            return el.text[len('xwiki:Studies.'):]

    def list(self):
        url = self.base + '/rest/patients?number=10000000'
        r = requests.get(url, auth=self.auth, headers={'Content-Type': 'application/xml'})
        r.raise_for_status()
        root = ElementTree.fromstring(r.text)
        id_elements = root.findall('./{https://phenotips.org/}patientSummary/{https://phenotips.org/}id')
        return list(map(lambda el: el.text, id_elements))

    def set(self, patient_id, patient_obj):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.PatientClass/0'
        data = {}
        for key in patient_obj:
            data['property#' + key] = patient_obj[key]
        r = requests.put(url, auth=self.auth, data=data)
        r.raise_for_status()

    def set_study(self, patient_id, study):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.StudyBindingClass/0'
        r = requests.get(url, auth=self.auth)
        if r.status_code == 404:
            if study == None:
                return
            else:
                url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects'
                data = {
                    'className': 'PhenoTips.StudyBindingClass',
                    'property#studyReference': 'xwiki:Studies.' + study,
                }
                r = requests.post(url, auth=self.auth, data=data)
                r.raise_for_status()
        else:
            r.raise_for_status()
            if study == None:
                requests.delete(url, auth=self.auth)
                r.raise_for_status()
            else:
                r = requests.put(url, auth=self.auth, data={studyReference: 'xwiki:Studies.' + study})
                r.raise_for_status()

