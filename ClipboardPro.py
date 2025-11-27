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
from PyQt6.QtWidgets import (QWidget, QPushButton, QLineEdit, QLabel,
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
        
        # Flag to prevent change detection when selecting items from app
        self.selecting_from_app = False
        
        # Store all items for search functionality
        self.all_items = []  # Store all clipboard items
        self.filtered_items = []  # Store filtered items for display
        
        # Auto-hide functionality
        self.search_visible = False
        self.buttons_visible = False

        self.setWindowTitle('Clipboard Pro')

        # get screen size and set app size
        # screen_resolution = QScreen.availableGeometry(self)
        self.screenW, self.screenH = 2600, 1200

        # set position
        self.setGeometry(int(self.screenW * 0.9), int(0), int(self.screenW * 0.1), int(self.screenH * 0.3))
        self.setWindowTitle('Clipboard Pro')
        #self.setStyleSheet("background-color: {}; color: {}; font-size: {}pt;".format(self.bg_col, self.color_odd, self.font_size))

        # create widgets with modern Mac-like styling
        delButton = QPushButton("Delete")
        delButton.setMinimumHeight(25)
        delButton.setMaximumWidth(90)
        delButton.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #6d6d70;
            }
            QPushButton:pressed {
                background-color: #48484a;
            }
        """)
        
        saveButton = QPushButton("Save")
        saveButton.setMinimumHeight(25)
        saveButton.setMaximumWidth(90)
        saveButton.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #11c733;
            }
            QPushButton:pressed {
                background-color: #11a711;
            }
        """)
        
        clrButton = QPushButton("Reset")
        clrButton.setMinimumHeight(25)
        clrButton.setMaximumWidth(90)
        clrButton.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #ff2d55;
            }
            QPushButton:pressed {
                background-color: #d70015;
            }
        """)
        
        plusButton = QPushButton("+")
        plusButton.setMinimumHeight(25)
        plusButton.setMaximumWidth(40)
        plusButton.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #6d6d70;
            }
            QPushButton:pressed {
                background-color: #48484a;
            }
        """)
        
        minButton = QPushButton("−")
        minButton.setMinimumHeight(25)
        minButton.setMaximumWidth(40)
        minButton.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #6d6d70;
            }
            QPushButton:pressed {
                background-color: #48484a;
            }
        """)
        
        # More button to show/hide search and buttons
        self.moreButton = QPushButton("⋯")
        self.moreButton.setStyleSheet("""
            QPushButton {
                background-color: #8e8e93;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                padding: 0px;
                width: 100px;
            }
            QPushButton:hover {
                background-color: #6d6d70;
            }
            QPushButton:pressed {
                background-color: #48484a;
            }
        """)
        # Install event filter for hover detection
        self.moreButton.installEventFilter(self)
        
        # Search bar
        searchLabel = QLabel("Search:")
        searchLabel.setMinimumHeight(20)
        searchLabel.setMaximumWidth(60)
        self.searchBar = QLineEdit()
        self.searchBar.setMinimumHeight(35)
        self.searchBar.setPlaceholderText("Search in clipboard...")
        
        # Style the search bar with rounder corners
        search_style = """
        QLineEdit {{
            background-color: {};
            color: {};
            font-size: {}pt;
            border: 2px solid #555555;
            border-radius: 5px;
            padding: 5px 10px 5px 10px;
            margin-left: 5px;
            margin-right: 5px;
        }}
        QLineEdit:focus {{
            border: 2px solid #0078d4;
        }}
        """.format(self.bg_col, self.color_odd, self.font_size)
        self.searchBar.setStyleSheet(search_style)
        
        # Add clear button inside the search bar
        self.clearSearchButton = QPushButton("×")
        self.clearSearchButton.setMaximumSize(22, 22)
        self.clearSearchButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8e8e93;
                border: none;
                font-size: 14px;
                font-weight: 600;
                border-radius: 11px;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #ff3b30;
                border-radius: 11px;
            }
            QPushButton:pressed {
                background-color: #d70015;
            }
        """)
        self.clearSearchButton.clicked.connect(self.clearSearch)
        self.clearSearchButton.hide()  # Initially hidden
        
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
        self.buttonContainer = QWidget()
        hbox = QHBoxLayout(self.buttonContainer)
        hbox.addWidget(delButton)
        hbox.addWidget(saveButton)
        hbox.addWidget(clrButton)
        hbox.addWidget(plusButton)
        hbox.addWidget(minButton)
        hbox.setSpacing(4)  # Add spacing between buttons
        hbox.setContentsMargins(6, 0, 6, 0)  # Add margins around the button row
        
        # Search bar layout
        self.searchContainer = QWidget()
        searchHbox = QHBoxLayout(self.searchContainer)
        searchHbox.addWidget(searchLabel)
        
        # Create a container for the search bar and clear button
        searchBarContainer = QWidget()
        searchContainerLayout = QHBoxLayout(searchBarContainer)
        searchContainerLayout.setContentsMargins(0, 0, 0, 0)
        searchContainerLayout.addWidget(self.searchBar)
        searchContainerLayout.addWidget(self.clearSearchButton)
        searchContainerLayout.setAlignment(self.clearSearchButton, QtCore.Qt.AlignmentFlag.AlignRight)
        
        searchHbox.addWidget(searchBarContainer)
        searchHbox.setContentsMargins(5, 5, 5, 5)
        
        # More button layout
        moreButtonLayout = QHBoxLayout()
        moreButtonLayout.addWidget(self.moreButton)
        moreButtonLayout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        moreButtonLayout.setContentsMargins(6, 3, 6, 3)

        # a vertical box with the clipboard and the horizontal box in it
        vbox = QVBoxLayout()
        vbox.addWidget(splitter)
        vbox.addWidget(self.clipboard)
        vbox.addWidget(self.searchContainer)
        vbox.addWidget(self.buttonContainer)
        vbox.addLayout(moreButtonLayout)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        
        # Initially hide search and button containers
        self.searchContainer.hide()
        self.buttonContainer.hide()
        
        # Install event filters for hover detection on containers
        self.searchContainer.installEventFilter(self)
        self.buttonContainer.installEventFilter(self)

        self.setLayout(vbox)

        # connect button to methods on_click
        delButton.clicked.connect(self.deleteItem)
        clrButton.clicked.connect(self.clearList)
        saveButton.clicked.connect(self.saveList)
        self.clipboard.clicked.connect(self.selectItem)
        self.clipboard.doubleClicked.connect(self.editItem)
        plusButton.clicked.connect(self.increase_font)
        minButton.clicked.connect(self.decrease_font)
        self.searchBar.textChanged.connect(self.onSearchTextChanged)

        #create instance of system clipboard
        self.CB = QApplication.clipboard()

        # Use clipboard change signal instead of timer for better performance
        self.CB.dataChanged.connect(self.onClipboardChanged)

        # Fallback timer with much longer interval for edge cases
        timer0 = QTimer(self)
        timer0.timeout.connect(self.checkClipboardChanges)
        timer0.start(1000)  # Check every 5 seconds instead of 200ms
        
        # Auto-hide timer
        self.autoHideTimer = QTimer(self)
        self.autoHideTimer.timeout.connect(self.autoHideWidgets)
        self.autoHideTimer.setSingleShot(True)

        self.show()

    def onClipboardChanged(self):
        """Handle clipboard changes via signal (more efficient than polling)"""
        # Don't add items when we're selecting from our own app
        if not self.selecting_from_app:
            self.addItem()

    def checkClipboardChanges(self):
        """Fallback method to check for clipboard changes (less frequent)"""
        # Don't check if we're selecting from our own app
        if self.selecting_from_app:
            return
            
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
            
        display_item = items[0]
        if hasattr(display_item, 'is_image') and display_item.is_image:
            # For images, we could show a preview dialog or just copy to clipboard
            self.selectItem()
        else:
            # For text items, find the original item in all_items and edit it
            text2edit = display_item.get_content()
            text, okPressed = QInputDialog.getText(self, "Get text", "Edit Clip:", text=text2edit)
            if okPressed and text != '':
                # Find and update the original item in all_items
                for original_item in self.all_items:
                    if (not hasattr(original_item, 'is_image') or not original_item.is_image) and original_item.get_content() == text2edit:
                        original_item.text_content = text
                        break
                
                # Update display
                self.updateDisplay()
                self.selectItem()

    def saveList(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)")
        if fileName:
            text_file = open(fileName, "w")
            text2save = ''
            for item in self.all_items:
                if hasattr(item, 'is_image') and item.is_image:
                    text2save += f"[Image] {item.image_path}\n"
                else:
                    text2save += item.get_content() + '\n'
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
                        
                        # Add to all_items list (for search functionality)
                        self.all_items.insert(0, item)
                        
                        # Update display based on current search
                        self.updateDisplay()
                        
                        self.lastImageHash = image_hash
                        self.lastMimeDataHash = mime_hash
                        if self.tray_icon:
                            self.tray_icon.last_content = f"[Image] {image_filename}"
        
        elif newClip != self.lastClip and newClip.strip():
            # Handle text content
            item = ImageListWidgetItem(text=newClip, is_image=False)
            
            # Add to all_items list (for search functionality)
            self.all_items.insert(0, item)
            
            # Update display based on current search
            self.updateDisplay()
            
            self.lastClip = newClip
            self.lastMimeDataHash = mime_hash
            if self.tray_icon:
                self.tray_icon.last_content = newClip

    def selectItem(self):
        items = self.clipboard.selectedItems()
        if not items:
            return
            
        item = items[0]
        
        # Set flag to prevent change detection when copying from our app
        self.selecting_from_app = True
        
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
        
        # Reset flag after a short delay to allow clipboard change to complete
        QTimer.singleShot(100, lambda: setattr(self, 'selecting_from_app', False))

    def deleteItem(self):
        listItems = self.clipboard.selectedItems()
        if not listItems:
            return
        
        # Find the corresponding items in all_items and remove them
        for display_item in listItems:
            # Find the original item in all_items by matching content
            for i, original_item in enumerate(self.all_items):
                if (hasattr(display_item, 'is_image') and hasattr(original_item, 'is_image') and 
                    display_item.is_image == original_item.is_image):
                    
                    if display_item.is_image:
                        # For images, match by image path
                        if (display_item.image_path == original_item.image_path):
                            # Delete image file if it's an image item
                            if original_item.image_path:
                                try:
                                    if os.path.exists(original_item.image_path):
                                        os.remove(original_item.image_path)
                                except:
                                    pass  # Ignore errors when deleting files
                            self.all_items.pop(i)
                            break
                    else:
                        # For text items, match by content
                        if display_item.get_content() == original_item.get_content():
                            self.all_items.pop(i)
                            break
        
        # Update display
        self.updateDisplay()

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
        for item in self.all_items:
            if hasattr(item, 'is_image') and item.is_image and item.image_path:
                try:
                    if os.path.exists(item.image_path):
                        os.remove(item.image_path)
                except:
                    pass  # Ignore errors when deleting files
        
        # Clear both the display and the stored items
        self.all_items.clear()
        self.clipboard.clear()
        self.searchBar.clear()  # Clear search bar as well
        self.clearSearchButton.hide()  # Hide clear button
        
        # Show the more button since we're hiding everything
        self.moreButton.show()

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

    def filterItems(self):
        """Filter clipboard items based on search text"""
        search_text = self.searchBar.text().lower()
        
        if not search_text:
            # If search is empty, show all items
            self.showAllItems()
            return
        
        # Clear current display
        self.clipboard.clear()
        
        # Filter items based on search text
        filtered_count = 0
        for i, item in enumerate(self.all_items):
            if hasattr(item, 'is_image') and item.is_image:
                # For images, search in filename
                searchable_text = item.image_path.lower() if item.image_path else ""
            else:
                # For text items, search in text content
                searchable_text = item.get_content().lower()
            
            if search_text in searchable_text:
                # Create a copy of the item for display
                if hasattr(item, 'is_image') and item.is_image:
                    display_item = ImageListWidgetItem(text=item.text_content, image_path=item.image_path, is_image=True)
                else:
                    display_item = ImageListWidgetItem(text=item.get_content(), is_image=False)
                
                self.clipboard.addItem(display_item)
                
                # Apply alternating colors
                if filtered_count % 2:
                    color = QtGui.QColor(self.color_even)
                    display_item.setForeground(QtGui.QBrush(color))
                
                filtered_count += 1

    def showAllItems(self):
        """Show all items in the clipboard"""
        self.clipboard.clear()
        
        for i, item in enumerate(self.all_items):
            # Create a copy of the item for display
            if hasattr(item, 'is_image') and item.is_image:
                display_item = ImageListWidgetItem(text=item.text_content, image_path=item.image_path, is_image=True)
            else:
                display_item = ImageListWidgetItem(text=item.get_content(), is_image=False)
            
            self.clipboard.addItem(display_item)
            
            # Apply alternating colors
            if i % 2:
                color = QtGui.QColor(self.color_even)
                display_item.setForeground(QtGui.QBrush(color))

    def updateDisplay(self):
        """Update the display based on current search filter"""
        search_text = self.searchBar.text().lower()
        
        if not search_text:
            self.showAllItems()
        else:
            self.filterItems()

    def onSearchTextChanged(self):
        """Handle search text changes and show/hide clear button"""
        search_text = self.searchBar.text()
        
        # Show/hide clear button based on whether there's text
        if search_text:
            self.clearSearchButton.show()
        else:
            self.clearSearchButton.hide()
        
        # Filter items
        self.filterItems()

    def clearSearch(self):
        """Clear the search bar and show all items"""
        self.searchBar.clear()
        self.clearSearchButton.hide()
        self.showAllItems()

    def onMoreButtonHover(self, event):
        """Show search and button containers when hovering over more button"""
        self.showWidgets()
        self.autoHideTimer.stop()  # Stop auto-hide timer when hovering

    def onMoreButtonLeave(self, event):
        """Start auto-hide timer when leaving more button"""
        self.autoHideTimer.start(5000)  # Auto-hide after 2 seconds

    def showWidgets(self):
        """Show search and button containers"""
        if not self.search_visible:
            self.searchContainer.show()
            self.search_visible = True
        if not self.buttons_visible:
            self.buttonContainer.show()
            self.buttons_visible = True
        
        # Hide the more button when widgets are shown
        self.moreButton.hide()

    def autoHideWidgets(self):
        """Auto-hide search and button containers"""
        if self.search_visible:
            self.searchContainer.hide()
            self.search_visible = False
        if self.buttons_visible:
            self.buttonContainer.hide()
            self.buttons_visible = False
        
        # Show the more button when widgets are hidden
        self.moreButton.show()

    def eventFilter(self, obj, event):
        """Handle hover events for the more button and containers"""
        if obj == self.moreButton:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.onMoreButtonHover(event)
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.onMoreButtonLeave(event)
        elif obj in [self.searchContainer, self.buttonContainer]:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.autoHideTimer.stop()  # Stop auto-hide when hovering over containers
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.autoHideTimer.start(2000)  # Start auto-hide timer when leaving containers
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ex = Clipboard()
    sys.exit(app.exec())
