#!/usr/bin/python3

from phenotipsbot import PhenoTipsBot
from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Q_ARG
from PyQt5.QtCore import QMetaObject
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMainWindow
from sys import argv
from sys import exit
from threading import Thread
parse_csv_file = __import__('import-csv').parse_csv_file
get_patient_ids = __import__('import-csv').get_patient_ids
import_patients = __import__('import-csv').import_patients
export_patients = __import__('export-csv').export_patients
get_clinvar_data = __import__('export-clinvar').get_clinvar_data
write_clinvar_files = __import__('export-clinvar').write_clinvar_files

IMPORT_CSV = 1
EXPORT_CSV = 2
EXPORT_CLINVAR = 3

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.statusLabel.setText("")
        self.progressBar.setVisible(False)
        self.previousButton.clicked.connect(self.previousButton_clicked)
        self.nextButton.clicked.connect(self.nextButton_clicked)
        self.siteSelector.lineEdit().returnPressed.connect(self.nextButton_clicked)
        self.usernameTextbox.returnPressed.connect(self.nextButton_clicked)
        self.passwordTextbox.returnPressed.connect(self.nextButton_clicked)
        self.importCsvOption.clicked.connect(self.operationOption_clicked)
        self.exportCsvOption.clicked.connect(self.operationOption_clicked)
        self.exportClinVarOption.clicked.connect(self.operationOption_clicked)
        self.browseButton.clicked.connect(self.browseButton_clicked)

    def asyncAddGeneSelectorItem(self, item):
        QMetaObject.invokeMethod(self, 'addGeneSelectorItem', Qt.QueuedConnection, Q_ARG(str, item))

    def asyncAddOwnerSelectorItem(self, item):
        QMetaObject.invokeMethod(self, 'addOwnerSelectorItem', Qt.QueuedConnection, Q_ARG(str, item))

    def asyncAddStudySelectorItem(self, item):
        QMetaObject.invokeMethod(self, 'addStudySelectorItem', Qt.QueuedConnection, Q_ARG(str, item))

    def asyncClearOwnerSelector(self):
        QMetaObject.invokeMethod(self.ownerSelector, 'clear', Qt.QueuedConnection)

    def asyncClearStudySelector(self):
        QMetaObject.invokeMethod(self.studySelector, 'clear', Qt.QueuedConnection)

    def asyncHideGeneSelector(self):
        QMetaObject.invokeMethod(self.geneLabel, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, False))
        QMetaObject.invokeMethod(self.geneSelector, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, False))

    def asyncLockUi(self, status, maxProgress = 0):
        QMetaObject.invokeMethod(self, 'setEnabled', Qt.QueuedConnection, Q_ARG(bool, False))
        self.asyncSetStatus(status, maxProgress)
        QMetaObject.invokeMethod(self.progressBar, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, True))

    def asyncResetGeneSelector(self):
        QMetaObject.invokeMethod(self.geneLabel, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, True))
        QMetaObject.invokeMethod(self.geneSelector, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, True))
        QMetaObject.invokeMethod(self.geneSelector, 'clear', Qt.QueuedConnection)
        self.asyncAddGeneSelectorItem('All genes')

    def asyncSetBrowseLabelText(self, text):
        QMetaObject.invokeMethod(self.browseLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, text))

    def asyncSetConfirmation(self, confirmation):
        QMetaObject.invokeMethod(self.confirmationLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, confirmation))

    def asyncSetOwnerLabelText(self, text):
        QMetaObject.invokeMethod(self.ownerLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, text))

    def asyncSetOwnerSelectorText(self, text):
        QMetaObject.invokeMethod(self.ownerSelector, 'setCurrentText', Qt.QueuedConnection, Q_ARG(str, text))

    def asyncSetPage(self, index):
        QMetaObject.invokeMethod(self.stackedWidget, 'setCurrentIndex', Qt.QueuedConnection, Q_ARG(int, index))

    def asyncSetProgress(self, progress):
        QMetaObject.invokeMethod(self.progressBar, 'setValue', Qt.QueuedConnection, Q_ARG(int, progress))

    def asyncSetStatus(self, status, maxProgress = 0):
        QMetaObject.invokeMethod(self.statusLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, status))
        QMetaObject.invokeMethod(self.progressBar, 'setMaximum', Qt.QueuedConnection, Q_ARG(int, maxProgress))

    def asyncSetStudyLabelText(self, text):
        QMetaObject.invokeMethod(self.studyLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, text))

    def asyncSetSummary(self, summary):
        QMetaObject.invokeMethod(self.summaryLabel, 'setText', Qt.QueuedConnection, Q_ARG(str, summary))

    def asyncUnlockUi(self, status = ''):
        QMetaObject.invokeMethod(self, 'setEnabled', Qt.QueuedConnection, Q_ARG(bool, True))
        QMetaObject.invokeMethod(self.progressBar, 'setVisible', Qt.QueuedConnection, Q_ARG(bool, False))
        self.asyncSetStatus(status)

    def turnToPage2(self):
        self.asyncLockUi('Finding studies, users, and work groups...')
        self.site = self.siteSelector.currentText().rstrip('/')
        self.username = self.usernameTextbox.text()
        self.password = self.passwordTextbox.text()
        self.bot = PhenoTipsBot(self.site, self.username, self.password)
        try:
            self.studies = self.bot.list_studies()
            self.users = self.bot.list_users()
            self.groups = self.bot.list_groups()
            self.gene_table = {}
            if self.operation == EXPORT_CLINVAR:
                self.asyncSetStatus('Getting patient list...')
                patient_ids = self.bot.list()
                self.asyncSetStatus('Getting gene list...', len(patient_ids))
                count = 0
                for patient_id in patient_ids:
                    for variant_num in self.bot.list_objects(patient_id, 'PhenoTips.ClinVarVariantClass'):
                        gene = self.bot.get_object(patient_id, 'PhenoTips.ClinVarVariantClass', variant_num).get('gene_symbol').upper()
                        if gene:
                            if gene not in self.gene_table:
                                self.gene_table[gene] = set()
                            self.gene_table[gene].add(patient_id)
                    count += 1
                    self.asyncSetProgress(count)
        except Exception as err:
            self.asyncUnlockUi(str(err))
            return
        if len(self.studies) or len(self.users) > 1 or len(self.groups):
            self.asyncClearStudySelector()
            self.asyncClearOwnerSelector()
            if self.operation == IMPORT_CSV:
                self.asyncSetStudyLabelText('Which study form should be used for the new patients?')
                self.asyncSetOwnerLabelText('Who should own (have access to) the new patients?')
            else:
                self.asyncSetStudyLabelText('Which study do you want to export from?')
                self.asyncAddStudySelectorItem('All studies')
                self.asyncSetOwnerLabelText('Which user or group\'s patients do you want to export?')
                self.asyncAddOwnerSelectorItem('All users')
            self.asyncAddStudySelectorItem('Default study')
            for study in self.studies:
                self.asyncAddStudySelectorItem(study)
            for user in self.users:
                self.asyncAddOwnerSelectorItem(user)
            for group in self.groups:
                self.asyncAddOwnerSelectorItem('Groups.' + group)
            if self.operation == IMPORT_CSV:
                self.asyncSetOwnerSelectorText(self.username)
        if self.operation == IMPORT_CSV:
            self.asyncHideGeneSelector()
            if len(self.users) > 1 or len(self.studies):
                self.asyncSetPage(2)
            else:
                self.study = None
                self.turnToPage3()
            self.asyncUnlockUi()
        elif self.operation == EXPORT_CSV:
            self.asyncHideGeneSelector()
            if len(self.studies) > 1:
                self.asyncSetPage(2)
            else:
                self.study = None
                self.turnToPage3()
            self.asyncUnlockUi()
        else:
            if len(self.gene_table):
                self.asyncResetGeneSelector()
                for gene in self.gene_table:
                    self.asyncAddGeneSelectorItem(gene)
                if len(self.studies) or len(self.gene_table) > 1:
                    self.asyncSetPage(2)
                else:
                    self.study = None
                    self.owner = self.username
                    self.gene = None
                    self.asyncTurnToPage3()
                self.asyncUnlockUi()
            else:
                self.asyncUnlockUi('There are no variants for ClinVar on this site.')

    def turnToPage3(self):
        if self.operation == IMPORT_CSV:
            self.asyncSetBrowseLabelText('Please click Browse and open the file to import.')
        elif self.operation == EXPORT_CSV:
            self.asyncSetBrowseLabelText('Please click Browse and save the file to export.')
        else:
            self.asyncSetBrowseLabelText('Please click Browse and select the folder to save Variant.csv and CaseData.csv to.')
        self.asyncSetPage(3)

    def turnToPage4(self):
        global confirmation
        self.asyncLockUi('Parsing CSV file...')
        confirmation = ''

        try:
            def unrecognizedColumnHandler(column):
                global confirmation
                confirmation += 'WARNING: Ignoring unrecognized column "' + column + '"\n'
            def unrecognizedValueHandler(value, field):
                global confirmation
                confirmation += 'WARNING: Ignoring unrecognized value "' + value + '" for "' + field + '"\n'

            self.patients = parse_csv_file(self.path, unrecognizedColumnHandler, unrecognizedValueHandler)

            self.asyncSetStatus('Checking ' + str(len(self.patients)) + ' external IDs...', len(self.patients))
            self.patient_ids = get_patient_ids(self.bot, self.patients, self.asyncSetProgress)
            self.n_to_import = str(len(self.patients) - len(self.patient_ids))
            self.n_to_update = str(len(self.patient_ids))
        except Exception as err:
            self.asyncUnlockUi(str(err))
            return

        confirmation += '\nYou are about to import ' + self.n_to_import + ' new patients and update ' + self.n_to_update + ' existing patients.'
        self.asyncSetConfirmation(confirmation.strip())
        self.asyncSetPage(4)
        self.asyncUnlockUi()

    def turnToPage5(self):
        if self.operation == IMPORT_CSV:
            self.asyncLockUi('Importing/updating...', len(self.patients))

            try:
                elapsedTime = import_patients(self.bot, self.patients, self.patient_ids, self.study, self.owner, self.asyncSetProgress)
            except Exception as err:
                self.asyncUnlockUi(str(err))
                return

            self.asyncSetSummary(
                'Imported ' + self.n_to_import + ' patients and updated ' + self.n_to_update + ' patients.\n' +
                'Elapsed time ' + str(elapsedTime)
            )
        elif self.operation == EXPORT_CSV:
            self.asyncLockUi('Getting patient list...')

            try:
                patient_ids = self.bot.list()
                self.asyncSetStatus('Exporting...', len(patient_ids))
                outFile = open(self.path, 'w')
                n_exported, elapsedTime = export_patients(self.bot, patient_ids, self.study, self.owner, outFile, self.asyncSetProgress)
                outFile.close()
            except Exception as err:
                self.asyncUnlockUi(str(err))
                return

            self.asyncSetSummary(
                'Exported ' + str(n_exported) + ' patients.\n' +
                'Elapsed time ' + str(elapsedTime))
        else:
            if self.gene:
                patient_ids = self.gene_table[self.gene]
            else:
                patient_ids = set.intersection(*self.gene_table.values())

            self.asyncLockUi('Exporting...', len(patient_ids))

            try:
                clinvar_data, elapsedTime1 = get_clinvar_data(self.bot, patient_ids, self.study, self.owner, self.gene, self.asyncSetProgress)

                self.asyncSetStatus('Writing files Variant.csv and CaseData.csv...')
                variantsFile = open(self.path + '/Variant.csv', 'w')
                caseDataFile = open(self.path + '/CaseData.csv', 'w')
                n_variants, n_cases, elapsedTime2 = write_clinvar_files(clinvar_data, variantsFile, caseDataFile)
                variantsFile.close()
                caseDataFile.close()
            except Exception as err:
                self.asyncUnlockUi(str(err))
                return

            self.asyncSetSummary(
                'Exported ' + str(n_variants) + ' variants and ' + str(n_cases) + ' cases.\n' +
                'Elapsed time ' + str(elapsedTime1 + elapsedTime2)
            )
        self.asyncSetPage(5)
        self.asyncUnlockUi()

    # slots #

    @pyqtSlot(str)
    def addGeneSelectorItem(self, item):
        self.geneSelector.addItem(item)

    @pyqtSlot(str)
    def addStudySelectorItem(self, item):
        self.studySelector.addItem(item)

    @pyqtSlot(str)
    def addOwnerSelectorItem(self, item):
        self.ownerSelector.addItem(item)

    def browseButton_clicked(self):
        if self.operation == IMPORT_CSV:
            path = QFileDialog.getOpenFileName(self, 'Import spreadsheet', '', '*.csv')[0]
        elif self.operation == EXPORT_CSV:
            path = QFileDialog.getSaveFileName(self, 'Export spreadsheet', '', '*.csv')[0]
        else:
            path = QFileDialog.getExistingDirectory(self, 'Export spreadsheets')
        if path:
            self.pathLabel.setText(path)

    def nextButton_clicked(self):
        if self.stackedWidget.currentIndex() == 0: #operation
            self.importMode = self.importCsvOption.isChecked()
            if self.importCsvOption.isChecked():
                self.operation = IMPORT_CSV
            elif self.exportCsvOption.isChecked():
                self.operation = EXPORT_CSV
            else:
                self.operation = EXPORT_CLINVAR
            self.previousButton.setEnabled(True)
            self.stackedWidget.setCurrentIndex(1) #login
        elif self.stackedWidget.currentIndex() == 1: #login
            Thread(target=self.turnToPage2).start() #study
        elif self.stackedWidget.currentIndex() == 2: #study, owner, and gene
            self.study = self.studySelector.currentText()
            if self.study == 'All studies':
                self.study = None
            elif self.study == 'Default study':
                if len(self.studies):
                    self.study = ''
                else:
                    self.study = None
            self.owner = self.ownerSelector.currentText()
            if self.owner == 'All users':
                self.owner = None
            self.gene = self.geneSelector.currentText()
            if self.gene == 'All genes':
                self.gene = None
            self.pathLabel.setText('')
            Thread(target=self.turnToPage3).start() #file
        elif self.stackedWidget.currentIndex() == 3: #file
            self.path = self.pathLabel.text()
            if self.path:
                if self.operation == IMPORT_CSV:
                    Thread(target=self.turnToPage4).start() #confirmation
                else:
                    Thread(target=self.turnToPage5).start() #summary
            else:
                self.browseButton_clicked()
        elif self.stackedWidget.currentIndex() == 4: #confirmation
            Thread(target=self.turnToPage5).start() #summary
        elif self.stackedWidget.currentIndex() == 5: #summary
            self.previousButton.setEnabled(False)
            self.stackedWidget.setCurrentIndex(0) #operation

    def operationOption_clicked(self):
        self.nextButton.setEnabled(True)

    def previousButton_clicked(self):
        self.statusLabel.clear()
        if self.stackedWidget.currentIndex() in [1, 5]: #login, summary
            self.stackedWidget.setCurrentIndex(0) #operation
            self.previousButton.setEnabled(False)
            self.nextButton.setEnabled(True)
        elif self.stackedWidget.currentIndex() == 2: #study
            self.stackedWidget.setCurrentIndex(1) #login
            self.previousButton.setEnabled(True)
            self.nextButton.setEnabled(True)
        elif self.stackedWidget.currentIndex() == 3: #file
            if len(self.studies):
                self.stackedWidget.setCurrentIndex(2) #study
            else:
                self.stackedWidget.setCurrentIndex(1) #login
            self.nextButton.setEnabled(True)
        elif self.stackedWidget.currentIndex() == 4: #confirmation
            self.stackedWidget.setCurrentIndex(3) #file

a = QApplication(argv)
w = MainWindow()
w.show()
exit(a.exec_())
