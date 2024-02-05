
#   Made by aciddev
#   Licensed under WTFPL
#   "if you dont like sushi i dont like you"
#   - aciddev

from email import message
from PySide6 import (
    QtWidgets,
    QtCore,
)
from tkinter import messagebox
from form import Ui_Form
from online import *
from gdsave import *
import traceback
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

        self.level = None
        
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

        # online
        self.ui.toolButton_3.clicked.connect(self.search)
        self.ui.listWidget_2.itemClicked.connect(self.selectLevel)
        self.ui.pushButton_6.clicked.connect(self.download)
        self.ui.pushButton_7.clicked.connect(self.downloadRaw)

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
        
    def search(self):
        search_list = 0
        if self.ui.radioButton_4.isChecked(): search_list = 1
        if self.ui.radioButton_3.isChecked(): search_list = 2
        
        search_type = 0
        if self.ui.radioButton_7.isChecked(): search_type = 1
        if self.ui.radioButton_6.isChecked(): search_type = 2

        search_res = search(self.ui.lineEdit.text(), search_list, search_type, self.ui.spinBox.value() - 1)

        self.ui.listWidget_2.clear()
        for i in search_res:
            item = QtWidgets.QListWidgetItem(i.name.decode())
            item.setData(QtCore.Qt.UserRole, i)
            self.ui.listWidget_2.addItem(item)
    
    def selectLevel(self, item):
        self.level = item.data(QtCore.Qt.UserRole)

        self.ui.lineEdit_2.setText(self.level.name.decode())
        self.ui.lineEdit_8.setText(self.level.description.decode())
    
    def download(self):
        if self.level is None:
            QtWidgets.QMessageBox.warning(self, "No level is selected", "To download select the level first!")
            return
        
        level = download_level(self.level.id)
        
        text, ok = QtWidgets.QFileDialog.getSaveFileName(self, "Save .ripped", "", "LevelRipper file (*.ripped)")
        if ok and text:
            open(text, "wb").write(level.serialize())
            QtWidgets.QMessageBox.information(self, "Success", "Level file successfuly exported!")
    
    def downloadRaw(self):
        if self.level is None:
            QtWidgets.QMessageBox.warning(self, "No level is selected", "To download select the level first!")
            return
        
        level = download_level(self.level.id)
        
        text, ok = QtWidgets.QFileDialog.getSaveFileName(self, "Save .txt", "", "Text file (*.txt)")
        if ok and text:
            open(text, "wb").write(level.level)
            QtWidgets.QMessageBox.information(self, "Success", "Level file successfuly exported!")

    def parseFile(self):
        file, error = parse_file(open(self.filePath, "rb"), self.ui.radioButton.isChecked())

        if error is not None:
            self.setLog(error)
            return
        
        self.file = file
        self.ui.lineEdit_3.setText(file.name.decode())
        self.ui.lineEdit_4.setText(file.description.decode())

    def setLog(self, text):
        self.ui.label_8.setText(text)

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    window = LevelRipper()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    try: main()
    except Exception as err:
        messagebox.showerror("Error occured", f"Error occured in application,\nplease report the bug into GitHub issues,\nattaching crash.log in program folder.\n\nDebug: {err}")
        open("crash.log", "w").write(traceback.format_exc())
