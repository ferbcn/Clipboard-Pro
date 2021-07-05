#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Clipboard Pro - Enhanced clipboard management with python
Dependencies: PyQt5 (GUI)
Author: Fernando Garcia Winterling

"""

import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QListWidget, QMainWindow, QSplitter, QFileDialog, QInputDialog, QLineEdit)
from PyQt5.QtCore import QTimer
from PyQt5.Qt import QApplication


class Clipboard(QWidget):

    def __init__(self):
        super().__init__()
        QMainWindow.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
        self.bg_col = "#404040"
        self.color_odd = '#aa88aa'
        self.color_even = '#778899'
        self.font_size = 14

        self.initUI()

    def initUI(self):

        self.lastClip = ''

        self.setWindowTitle('Clipboard Pro')

        # get screen size and set app size
        screen_resolution = app.desktop().screenGeometry()
        self.screenW, self.screenH = screen_resolution.width(), screen_resolution.height()

        # set position
        self.setGeometry(int(self.screenW * 0.9), int(0), int(self.screenW * 0.1), int(self.screenH * 0.3))
        self.setWindowTitle('Clipboard Pro')
        #self.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))

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
        plusButton = QPushButton("+")
        plusButton.setMinimumHeight(20)
        plusButton.setMaximumWidth(40)
        minButton = QPushButton("-")
        minButton.setMinimumHeight(20)
        minButton.setMaximumWidth(40)
        splitter = QSplitter(self)

        self.clipboard = QListWidget()
        self.clipboard.setMinimumHeight(int(self.screenH * 0.05))
        self.clipboard.setMinimumWidth(int(self.screenW * 0.1))
        #self.clipboard.setAlternatingRowColors(True)
        self.clipboard.setFocusPolicy(1) #remove blue frame when window is selected yeaaaah!
        self.clipboard.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))

        # define layout: a horizontal box with three buttons in it
        hbox = QHBoxLayout()
        hbox.addWidget(delButton)
        hbox.addWidget(saveButton)
        hbox.addWidget(clrButton)
        hbox.addWidget(plusButton)
        hbox.addWidget(minButton)
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
        plusButton.clicked.connect(self.increase_font)
        minButton.clicked.connect(self.decrease_font)

        #create instance of system clipboard
        self.CB = QApplication.clipboard()

        # timer to check for new content on clipboard
        # TODO: make this happen without timer
#        self.CB.dataChanged.connect(self.addItem) #DOES NOT WORK???

        timer0 = QTimer(self)
        timer0.timeout.connect(self.addItem)
        timer0.start(200)

        self.show()

    def increase_font(self):
        if self.font_size < 48:
            self.font_size += 2
        self.clipboard.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))

    def decrease_font(self):
        if self.font_size > 6:
            self.font_size -= 2
        self.clipboard.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))

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
        if newClip == self.lastClip:
            pass
        else:
            self.clipboard.insertItem(0, newClip)
            if not len(self.clipboard) % 2:
                color = QtGui.QColor(self.color_even)
                self.clipboard.item(0).setForeground(QtGui.QBrush(color))
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
        self.draw_rows()

    def draw_rows(self):
        # give rows correct alternating colors
        for row_num in range(self.clipboard.count()):
            if row_num % 2:
                color = QtGui.QColor(self.color_even)
            else:
                color = QtGui.QColor(self.color_odd)
            self.clipboard.item(row_num).setForeground(QtGui.QBrush(color))

    def clearList(self):
        self.clipboard.clear()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Clipboard()
    sys.exit(app.exec_())
