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

import io
import json
import requests
from base64 import b64encode
from selenium import webdriver
from xml.etree import ElementTree

class PhenoTipsBot:
    TIMEOUT = 20 #seconds

    driver = None

    def __init__(self, base_url, username, password):
        self.base = base_url
        self.auth = (username, password)

    def create(self, patient_obj=None, study=None, pedigree=None):
        r = requests.post(self.base + '/rest/patients', auth=self.auth)
        r.raise_for_status()
        patient_id = r.headers['location']
        patient_id = patient_id[patient_id.rfind('/')+1:]
        if patient_obj:
            self.set(patient_id, patient_obj)
        if study:
            self.set_study(patient_id, study)
        if pedigree:
            self.set_pedigree(patient_id, pedigree)
        #the mandatory PhenoTips.VCF object is not added until someone visits the edit page
        url = self.base + '/bin/edit/data/' + patient_id
        r = requests.get(url, auth=self.auth);
        r.raise_for_status()
        return patient_id

    def delete(self, patient_id):
        r = requests.delete(self.base + '/rest/patients/' + patient_id, auth=self.auth)
        r.raise_for_status()

    def export_pedigree_ped(self, patient_id, id_generation='external'):
        self.init_phantom()
        url = self.base + '/bin/' + patient_id + '?sheet=PhenoTips.PedigreeEditor'
        self.driver.get(url)
        self.driver.find_element_by_css_selector('#canvas svg') #wait for the page to load
        return self.driver.execute_script('return window.PedigreeExport.exportAsPED(window.editor.getGraph().DG, ' + json.dumps(id_generation) + ');')

    def get(self, patient_obj):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.PatientClass/0/properties'
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        root = ElementTree.fromstring(r.text)
        ret = {}
        for prop in root.iter('{http://www.xwiki.org}property'):
            ret[prop.attrib['name']] = prop.find('{http://www.xwiki.org}value').text
        return ret

    def get_pedigree(self, patient_id):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.PedigreeClass/0'
        r = requests.get(url, auth=self.auth)
        r.raise_for_status()
        tree = ElementTree.parse(io.StringIO(r.text))
        el = tree.find('{http://www.xwiki.org}property[@name="data"]/{http://www.xwiki.org}value')
        return json.loads(el.text)

    def get_study(self, patient_id):
        url = self.base + '/rest/wikis/xwiki/spaces/data/pages/' + patient_id + '/objects/PhenoTips.StudyBindingClass/0'
        r = requests.get(url, auth=self.auth)
        if r.status_code == 404:
            return None
        else:
            r.raise_for_status()
            tree = ElementTree.parse(io.StringIO(r.text))
            el = tree.find('{http://www.xwiki.org}property[@name="studyReference"]/{http://www.xwiki.org}value')
            return el.text[len('xwiki:Studies.'):]

    def import_pedigree_ped(self, patient_id, pedigree_str, mark_evaluated=False, external_id_mark=True, accept_unknown_phenotypes=True):
        self.init_phantom()
        url = self.base + '/bin/' + patient_id + '?sheet=PhenoTips.PedigreeEditor'
        data = json.dumps(pedigree_str)
        import_options = json.dumps({
            'markEvaluated': mark_evaluated,
            'externalIdMark': external_id_mark,
            'acceptUnknownPhenotypes': accept_unknown_phenotypes
        })
        self.driver.get(url)
        self.driver.find_element_by_css_selector('#canvas svg') #wait for the page to load
        self.driver.execute_script('window.editor.getSaveLoadEngine().createGraphFromImportData(' + data + ', "ped", ' + import_options + ');')
        self.driver.execute_script('window.editor.getSaveLoadEngine().save();')
        self.driver.find_element_by_css_selector('#action-save.menu-item') #wait for the image to be saved

    def init_phantom(self):
        if not self.driver:
            authorization = 'Basic ' + b64encode((self.auth[0] + ':' + self.auth[1]).encode('utf-8')).decode('utf-8')
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.authorization'] = authorization
            self.driver = webdriver.PhantomJS()
            self.driver.set_window_size(1920, 1080) #big enough to not cut off any elements
            self.driver.implicitly_wait(PhenoTipsBot.TIMEOUT)

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

    def set_pedigree(self, patient_id, pedigree_obj):
        #the SVG is not automatically updated if the JSON is changed via the REST API
        self.init_phantom()
        url = self.base + '/bin/' + patient_id + '?sheet=PhenoTips.PedigreeEditor'
        data = json.dumps(json.dumps(pedigree_obj, sort_keys=True))
        self.driver.get(url)
        self.driver.find_element_by_css_selector('#canvas svg') #wait for the page to load
        self.driver.execute_script('window.editor.getSaveLoadEngine().createGraphFromSerializedData(' + data + ');')
        self.driver.execute_script('window.editor.getSaveLoadEngine().save();')
        self.driver.find_element_by_css_selector('#action-save.menu-item') #wait for the image to be saved

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

