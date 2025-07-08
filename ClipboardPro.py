#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Clipboard Pro - Enhanced clipboard management with python
Dependencies: PyQt6 (GUI)
Author: Fernando Garcia Winterling

"""

import sys
import os
import uuid
from datetime import datetime
from PyQt6 import QtCore, QtGui
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QListWidget, QMainWindow, QSplitter, QFileDialog, QInputDialog,
                             QApplication, QListWidgetItem)
from PyQt6.QtCore import QTimer, QSize

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu


def get_system_theme():
    """Detect system theme and return 'dark' or 'light'"""
    app = QApplication.instance()
    if app is None:
        return 'dark'  # Default to dark theme
    
    # Get the application's palette
    palette = app.palette()
    background_color = palette.color(QtGui.QPalette.ColorRole.Window)
    
    # Calculate luminance to determine if it's dark or light
    # Using the standard luminance formula: 0.299*R + 0.587*G + 0.114*B
    luminance = (0.299 * background_color.red() + 
                 0.587 * background_color.green() + 
                 0.114 * background_color.blue()) / 255
    
    return 'dark' if luminance < 0.5 else 'light'


class ImageListWidgetItem(QListWidgetItem):
    def __init__(self, text="", image_path=None, is_image=False):
        super().__init__()
        self.text_content = text
        self.image_path = image_path
        self.is_image = is_image
        
        if is_image and image_path:
            # Create thumbnail for display
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to thumbnail size
                thumbnail = pixmap.scaled(64, 64, QtCore.Qt.AspectRatioMode.KeepAspectRatio, 
                                        QtCore.Qt.TransformationMode.SmoothTransformation)
                self.setIcon(QIcon(thumbnail))
                #self.setText(f"[Image] {os.path.basename(image_path)}")
            else:
                self.setText(f"[Image] {text}")
        else:
            self.setText(text)
    
    def get_content(self):
        if self.is_image:
            return self.image_path
        else:
            return self.text_content


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.parent = parent
        self.icon = icon
        self.menu = QMenu(parent)
        self.setIcon(icon)
        self.setVisible(True)

        self.last_content = ""

        show = self.menu.addAction("Last Clip")
        show.triggered.connect(self.show_mes)
        showAction = self.menu.addAction("Show")
        showAction.triggered.connect(self.show_action)
        exitAction = self.menu.addAction("Exit")
        exitAction.triggered.connect(self.exit_action)
        self.setContextMenu(self.menu)
        self.setToolTip("ClipboardPro")

    def show_mes(self):
        self.showMessage("ClipboardPro", f"{self.last_content}", self.icon, 2000)

    def show_action(self):
        self.parent.close()
        self.parent.show()

    def exit_action(self):
        self.parent.close()
        sys.exit()


class Clipboard(QWidget):

    def __init__(self):
        super().__init__()
        QMainWindow.__init__(self, None, QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.bg_col = "#404040"
        self.color_odd = '#aa88aa'
        self.color_even = '#778899'
        self.font_size = 14

        # Create images directory if it doesn't exist
        self.images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clipboard_images")
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        else:
            # Clean up old image files on startup
            self.cleanup_old_images()

        self.initUI()

    def initUI(self):

        # Create the icon based on system theme
        theme = get_system_theme()
        print(f"Detected system theme: {theme}")
        if theme == 'dark':
            icon_path = "icon_wb_s.png"  # Light theme: white background, black icon
        else:
            icon_path = "icon_bw_s.png"  # Dark theme: black background, white icon
        
        icon = QIcon(icon_path)
        
        # Check if icon loaded successfully
        if icon.isNull():
            print(f"Warning: Could not load icon file '{icon_path}'")
            # Try the other icon as fallback
            fallback_path = "icon_wb_s.png" if theme == 'dark' else "icon_bw_s.png"
            icon = QIcon(fallback_path)
            if icon.isNull():
                print(f"Warning: Could not load fallback icon file '{fallback_path}'")
                # Try to create a default icon
                icon = QIcon()
        
        # Check if system tray is supported
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system")
            self.tray_icon = None
        else:
            self.tray_icon = SystemTrayIcon(icon, parent=self)

        self.lastClip = ''
        self.lastImageHash = None
        self.lastMimeDataHash = None  # Track MIME data changes

        self.setWindowTitle('Clipboard Pro')

        # get screen size and set app size
        # screen_resolution = QScreen.availableGeometry(self)
        self.screenW, self.screenH = 2600, 1200

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
        # self.clipboard.setFocusPolicy(1) #remove blue frame when window is selected yeaaaah!
        self.clipboard.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))
        
        # Set icon size for image thumbnails
        self.clipboard.setIconSize(QSize(64, 64))

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

        # Use clipboard change signal instead of timer for better performance
        self.CB.dataChanged.connect(self.onClipboardChanged)

        # Fallback timer with much longer interval for edge cases
        timer0 = QTimer(self)
        timer0.timeout.connect(self.checkClipboardChanges)
        timer0.start(1000)  # Check every 5 seconds instead of 200ms

        self.show()

    def onClipboardChanged(self):
        """Handle clipboard changes via signal (more efficient than polling)"""
        self.addItem()

    def checkClipboardChanges(self):
        """Fallback method to check for clipboard changes (less frequent)"""
        # Only check if we haven't detected changes via signal
        newClip = self.CB.text()
        mimeData = self.CB.mimeData()
        
        # Simple hash of MIME data to detect changes
        mime_hash = self._getMimeDataHash(mimeData)
        
        if (newClip != self.lastClip and newClip.strip()) or mime_hash != self.lastMimeDataHash:
            self.addItem()

    def _getMimeDataHash(self, mimeData):
        """Create a simple hash of MIME data to detect changes efficiently"""
        if mimeData.hasImage():
            # For images, use a simpler approach - just check if image exists
            image = self.CB.image()
            if not image.isNull():
                # Use image size and format as a simple hash
                return f"{image.width()}_{image.height()}_{image.format()}"
        elif mimeData.hasText():
            # For text, use the text itself as hash
            return mimeData.text()
        return ""

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
        if not items:
            return
            
        item = items[0]
        if hasattr(item, 'is_image') and item.is_image:
            # For images, we could show a preview dialog or just copy to clipboard
            self.selectItem()
        else:
            # For text items
            text2edit = item.text()
            text, okPressed = QInputDialog.getText(self, "Get text", "Edit Clip:", text=text2edit)
            if okPressed and text != '':
                item.setText(text)
                item.text_content = text
                self.selectItem()

    def saveList(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)")
        if fileName:
            text_file = open(fileName, "w")
            n = self.clipboard.count()
            text2save = ''
            for i in range(n):
                item = self.clipboard.item(i)
                if hasattr(item, 'is_image') and item.is_image:
                    text2save += f"[Image] {item.image_path}\n"
                else:
                    text2save += item.text() + '\n'
            text_file.write(text2save)
            text_file.close()

    def addItem(self):
        # Check for text content
        newClip = self.CB.text()
        
        # Check for image content
        mimeData = self.CB.mimeData()
        hasImage = mimeData.hasImage()
        
        # Update MIME data hash
        mime_hash = self._getMimeDataHash(mimeData)
        
        if hasImage:
            # Get image from clipboard
            image = self.CB.image()
            if not image.isNull():
                # Use simpler hash method for better performance
                image_hash = f"{image.width()}_{image.height()}_{image.format()}"
                
                if image_hash != self.lastImageHash:
                    # Save image to file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_id = str(uuid.uuid4())[:8]
                    image_filename = f"clipboard_image_{timestamp}_{unique_id}.png"
                    image_path = os.path.join(self.images_dir, image_filename)
                    
                    if image.save(image_path, "PNG"):
                        # Create list item with image
                        item = ImageListWidgetItem(text=image_filename, image_path=image_path, is_image=True)
                        self.clipboard.insertItem(0, item)
                        
                        if not len(self.clipboard) % 2:
                            color = QtGui.QColor(self.color_even)
                            item.setForeground(QtGui.QBrush(color))
                        
                        self.lastImageHash = image_hash
                        self.lastMimeDataHash = mime_hash
                        if self.tray_icon:
                            self.tray_icon.last_content = f"[Image] {image_filename}"
        
        elif newClip != self.lastClip and newClip.strip():
            # Handle text content
            item = ImageListWidgetItem(text=newClip, is_image=False)
            self.clipboard.insertItem(0, item)
            
            if not len(self.clipboard) % 2:
                color = QtGui.QColor(self.color_even)
                item.setForeground(QtGui.QBrush(color))
            
            self.lastClip = newClip
            self.lastMimeDataHash = mime_hash
            if self.tray_icon:
                self.tray_icon.last_content = newClip

    def selectItem(self):
        items = self.clipboard.selectedItems()
        if not items:
            return
            
        item = items[0]
        
        if hasattr(item, 'is_image') and item.is_image:
            # Load image from file and put it in clipboard
            if item.image_path and os.path.exists(item.image_path):
                image = QImage(item.image_path)
                if not image.isNull():
                    self.CB.setImage(image)
                    # Update the hash using the same method as addItem
                    self.lastImageHash = f"{image.width()}_{image.height()}_{image.format()}"
        else:
            # Handle text content
            text2clip = item.get_content()
            self.CB.setText(text2clip)
            self.lastClip = text2clip

    def deleteItem(self):
        listItems = self.clipboard.selectedItems()
        if not listItems:
            return
        for item in listItems:
            # Delete image file if it's an image item
            if hasattr(item, 'is_image') and item.is_image and item.image_path:
                try:
                    if os.path.exists(item.image_path):
                        os.remove(item.image_path)
                except:
                    pass  # Ignore errors when deleting files
            
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
        # Delete all image files before clearing
        for i in range(self.clipboard.count()):
            item = self.clipboard.item(i)
            if hasattr(item, 'is_image') and item.is_image and item.image_path:
                try:
                    if os.path.exists(item.image_path):
                        os.remove(item.image_path)
                except:
                    pass  # Ignore errors when deleting files
        
        self.clipboard.clear()

    def cleanup_old_images(self):
        """Clean up old image files from the clipboard_images directory"""
        try:
            for filename in os.listdir(self.images_dir):
                if filename.startswith("clipboard_image_") and filename.endswith(".png"):
                    file_path = os.path.join(self.images_dir, filename)
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old image: {filename}")
                    except OSError as e:
                        print(f"Could not remove {filename}: {e}")
        except OSError as e:
            print(f"Error cleaning up images directory: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ex = Clipboard()
    sys.exit(app.exec())
