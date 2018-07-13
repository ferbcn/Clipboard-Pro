#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Clipboard Pro - Enhanced clipboard management with python
Dependencies: PyQt5 (GUI)
Author: Fernando Garcia Winterling

"""

import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QListWidget, QMainWindow, QSplitter, QFileDialog, QMessageBox, QInputDialog, QLineEdit)
from PyQt5.QtCore import QTimer, QSize
from PyQt5.Qt import QApplication


class Example(QWidget):

    def __init__(self):
        super().__init__()
        QMainWindow.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
        self.initUI()

    def initUI(self):

        self.lastClip = ''

        self.setWindowTitle('Clipboard Pro')

        # get screen size and set app size
        screen_resolution = app.desktop().screenGeometry()
        self.screenW, self.screenH = screen_resolution.width(), screen_resolution.height()

        # set position
        self.setGeometry(self.screenW * 0.9, 0, self.screenW * 0.1, self.screenH * 0.3)
        self.setWindowTitle('Clipboard Pro')

        # create widgets
        delButton = QPushButton("Delete")
        delButton.setMinimumHeight(20)
        delButton.setMaximumWidth(90)
        saveButton = QPushButton("Save")
        saveButton.setMinimumHeight(20)
        saveButton.setMaximumWidth(90)
        clrButton = QPushButton("Reset")
        clrButton.setMinimumHeight(20)
        clrButton.setMaximumWidth(90)
        splitter = QSplitter(self)

        self.clipboard = QListWidget()
        self.clipboard.setMinimumHeight(self.screenH * 0.05)
        self.clipboard.setMinimumWidth(self.screenW * 0.1)
        self.clipboard.setAlternatingRowColors(True)
        self.clipboard.setFocusPolicy(1) #remove blue frame when window is selected yeaaaah!

        # define layout: a horizontal box with two buttons in it
        hbox = QHBoxLayout()
        hbox.addWidget(delButton)
        hbox.addWidget(saveButton)
        hbox.addWidget(clrButton)
        hbox.setContentsMargins(0, 0, 0, 0)

        # a vertical box with the clipboard and the horizontal box in it
        vbox = QVBoxLayout()
        vbox.addWidget(splitter)
        vbox.addWidget(self.clipboard)
        vbox.addLayout(hbox)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(vbox)

        # connect button to methods on_click
        delButton.clicked.connect(self.deleteItem)
        clrButton.clicked.connect(self.clearList)
        saveButton.clicked.connect(self.saveList)
        self.clipboard.clicked.connect(self.selectItem)
        self.clipboard.doubleClicked.connect(self.editItem)

        #create instance of system clipboard
        self.CB = QApplication.clipboard()

        # timer to check for new content on clipboard
        # TODO: make this happen without timer
#        self.CB.dataChanged.connect(self.addItem) #DOES NOT WORK???

        timer0 = QTimer(self)
        timer0.timeout.connect(self.addItem)
        timer0.start(200)

        self.show()

    def editItem(self):
        items = self.clipboard.selectedItems()
        text2edit = items[0].text()
        text, okPressed = QInputDialog.getText(self, "Get text", "Edit Clip:", QLineEdit.Normal, text2edit)
        if okPressed and text != '':
            items[0].setText(text)
            self.selectItem()

    def saveList(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)")
        if fileName:
            text_file = open(fileName, "w")
            n = self.clipboard.count()
            text2save = ''
            for i in range(n):
                text2save += self.clipboard.item(i).text()
                text2save += '\n'
            text_file.write(text2save)
            text_file.close()

    def addItem(self):

        newClip = self.CB.text()
        #print(newClip)
        if newClip == self.lastClip:
            pass
        else:
            self.clipboard.insertItem(0, newClip)
            self.lastClip = newClip

    def selectItem(self):

        items = self.clipboard.selectedItems()
        text2clip = ''
        for item in items:
            text2clip += item.text()
            self.CB.setText(text2clip, 0)
        self.lastClip = text2clip

    def deleteItem(self):
        listItems = self.clipboard.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.clipboard.takeItem(self.clipboard.row(item))

    def clearList(self):
        self.clipboard.setCurrentItem(self.clipboard.item(0))
        for i in range(self.clipboard.count()):
            self.deleteItem()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
