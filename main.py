
#   Made by aciddev
#   Licensed under WTFPL
#   "if you dont like sushi i dont like you"
#   - aciddev

from PySide6 import (
    QtWidgets,
    QtCore,
    QtGui
)
from tkinter import messagebox
from form import Ui_Form
from gdsave import *
import psutil
import sys
import os

def process_exists(name):
    for i in psutil.process_iter():
        if i.name() == name: return True
    return False

def errorbox(title, content):
    messagebox.showerror(title, content)

if process_exists("GeometryDash.exe"):
    errorbox("GD is running!", "Close GD before using this program, as it uses savefile while this program processes/overwrittes it.")
    sys.exit(1)

if not os.path.isfile(os.path.join(os.getenv("LocalAppData"), gd_folder, "CCLocalLevels.dat")):
    errorbox("No savefile!", "Cant find a sevefile. Do you have GD installed?")
    sys.exit(1)

reload_save()

class LevelRipper(QtWidgets.QWidget):
    def __init__(self):
        super(LevelRipper, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.levels = []
        self.levelSelected = -1

        self.file = None
        self.filePath = None
        
        self.ui.lineEdit_5.setText(gd_folder)
        self.setGdFolder()

        self.connect()

        self.updateLevels()

    def connect(self):
        # export tab
        self.ui.checkBox.clicked.connect(lambda: self.toggleRawMode(self.ui.checkBox.isChecked()))
        self.ui.toolButton_2.clicked.connect(self.updateLevels)
        self.ui.listWidget.itemClicked.connect(self.selectItem)
        self.ui.pushButton.clicked.connect(self.saveLevel)
        self.ui.pushButton_2.clicked.connect(self.saveRawLevel)

        # import tab
        self.ui.toolButton.clicked.connect(self.browseFile)
        self.ui.pushButton_3.clicked.connect(self.parseFile)
        self.ui.pushButton_4.clicked.connect(self.importLevel)

        # settings
        self.ui.lineEdit_5.textChanged.connect(self.setGdFolder)
        self.ui.pushButton_5.clicked.connect(reload_save)

    def setGdFolder(self):
        global gd_folder
        gd_folder = self.ui.lineEdit_5.text()

    def toggleRawMode(self, is_on):
        self.ui.pushButton_2.setEnabled(is_on)
        self.ui.radioButton.setEnabled(is_on)

    def updateLevels(self):
        self.levels = export_levels()

        self.ui.listWidget.clear()
        for i in self.levels:
            item = QtWidgets.QListWidgetItem(i.name.decode())
            item.setData(QtCore.Qt.UserRole, i)
            self.ui.listWidget.addItem(item)

    def selectItem(self, item):
        self.levelSelected = self.ui.listWidget.row(item)
        level = item.data(QtCore.Qt.UserRole)
        self.ui.lineEdit_6.setText(level.name.decode())
        self.ui.lineEdit_7.setText(level.description.decode() if level.description != b"" else "None")

    def saveLevel(self):
        if self.levelSelected == -1:
            QtWidgets.QMessageBox.warning(self, "No level is selected", "To save file select the level first!")
            return
        
        text, ok = QtWidgets.QFileDialog.getSaveFileName(self, "Save .ripped", "", "LevelRipper file (*.ripped)")
        if ok and text:
            open(text, "wb").write(self.levels[self.levelSelected].serialize())
            QtWidgets.QMessageBox.information(self, "Success", "Level file successfuly exported!")

    def saveRawLevel(self):
        if self.levelSelected == -1:
            QtWidgets.QMessageBox.warning(self, "No level is selected", "To save file select the level first!")
            return
        
        text, ok = QtWidgets.QFileDialog.getSaveFileName(self, "Save .txt", "", "Text file (*.txt)")
        if ok and text:
            open(text, "wb").write(self.levels[self.levelSelected].level)
            QtWidgets.QMessageBox.information(self, "Success", "Level file successfuly exported!")

    def browseFile(self):
        text, ok = QtWidgets.QFileDialog.getOpenFileName(self, "Open .ripped or .txt", "", "LevelRipper file (*.ripped);;Text file (*.txt);;All files (*)")
        if text and ok:
            self.ui.label_7.setText(os.path.basename(text))

            self.filePath = text
        
        self.parseFile()
        
    def importLevel(self):
        if self.file is None:
            QtWidgets.QMessageBox.warning(self, "No level is selected", "To save file select the level first!")
            return

        import_level(self.file)    
        QtWidgets.QMessageBox.information(self, "Success", "Level file successfuly imported!")
        
    def parseFile(self):
        file, error = parse_file(open(self.filePath, "rb"), self.ui.radioButton.isChecked())

        if error is not None:
            self.setLog(error)
            return
        
        self.file = file
        self.ui.lineEdit_3.setText(file.name.decode())
        self.ui.lineEdit_4.setText(file.description.decode())

    def setLog(self, text):
        self.label_8.setText(text)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = LevelRipper()
    window.show()

    sys.exit(app.exec())
