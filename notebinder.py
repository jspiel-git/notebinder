#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Note Binder - a simple tool to organize text files

Author: Jérôme Spielmann
Website: jeromespielmann.com

MIT License

Copyright (c) 2020 Jérôme Spielmann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys

import datetime

import sqlite3

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *


class myListWidget(QListWidget):

   def getEntries(self):

      """
      Checks the database and returns the list with the elements of the database.
      """

      database = "notelist.db"
      conn = sqlite3.connect(database)
      cur = conn.cursor()  
      sql = "SELECT * FROM note;"
      cur.execute(sql) 
      rows = cur.fetchall() 
      conn.close()

      return rows

   def clicked(self, item):
      """
      When clicked set current item to selected item
      """

      self.setCurrentItem(item)

      #print('Clicked row: %s' % self.currentRow())

   def doubleClicked(self, item):
      """
      Opens the associated text file.
      """

      # Fixes the index of the current row.
      self.setCurrentItem(item)
      number = self.currentRow()

      # Select text file information
      if number == 0:

         textfile = "note-binder-info.txt"

      else:

         database = "notelist.db"
         conn = sqlite3.connect(database)
         cur = conn.cursor() 
         sql = "SELECT * FROM note LIMIT ?,?;" 
         cur = conn.execute(sql, [number, number])
         rows = cur.fetchall()
         conn.close()

         textfile = "note" + "-" + rows[0][2] + "-" + str(rows[0][3]) + ".txt"

      # Opens the text file using the terminal
      path = os.path.abspath(os.getcwd())
      path = os.path.join(path, "text-files", textfile)

      # Here code needs to change for other operating systems this works only on mac os
      os.system('open ' + path) 

   def addNote(self):
      """
      Creates a new entry into the SQL table and a new text file.
      """

      # Create unique random name file
      note_date = str(datetime.datetime.now().date())
      note_uniq = int(datetime.datetime.now().microsecond)

      # Create entry in database
      entry = ["New note", str(note_date), note_uniq]

      database = "notelist.db"
      conn = sqlite3.connect(database)
      sql = "INSERT INTO note (noteName, noteDate, fileId) VALUES (?,?,?);"
      conn.execute(sql, entry)
      conn.commit()
      conn.close()

      # Add item to the QlistQiwdget
      self.addItem("New note")

      # Create file
      path = os.path.abspath(os.getcwd())  
      path = os.path.join(path, "text-files", "note-{}-{}.txt".format(note_date, str(note_uniq)))
      os.system("echo Thoughts here. > {}".format(path))

   def removeNote(self):
      """
      Removes entry from database and associated text file.
      """

      number = self.currentRow()

      # Remove entry from database
      if number == 0:

         # We have to change the SQL code below it does not work for first row
         pass

      else:

         # Select text file information
         database = "notelist.db"
         conn = sqlite3.connect(database)
         cur = conn.cursor()  
         sql = "SELECT * FROM note LIMIT ?,?;"
         cur = conn.execute(sql, [number, number])
         rows = cur.fetchall() 
         conn.close()

         textfile = "note" + "-" + rows[0][2] + "-" + str(rows[0][3]) + ".txt"

         # Remove entry from database
         database = "notelist.db"
         conn = sqlite3.connect(database)
         sql = """DELETE FROM note 
                  WHERE noteId = (SELECT noteId FROM (SELECT noteId FROM note ORDER BY noteId LIMIT ?,?) AS t);"""
         conn.execute(sql, [number, number])
         conn.commit()
         conn.close()

         # Remove item from the QlistQiwdget
         self.takeItem(number)

         # Remove file
         path = os.path.abspath(os.getcwd())
         path = os.path.join(path, "text-files", textfile)
         os.system("rm {}".format(path))

   def onDataChanged(self):
      """
      On click on the change button while seleced.
      """

      number = self.currentRow()

      new_item = self.currentItem()

      # Change the name in the database
      database = "notelist.db"
      conn = sqlite3.connect(database)
      sql = """UPDATE note SET noteName = ? 
               WHERE noteId = (SELECT noteId FROM (SELECT noteId FROM note ORDER BY noteId LIMIT ?,?) AS t);"""
      conn.execute(sql, [new_item.text(), number, number])
      conn.commit()
      conn.close()

   def changeNote(self):
      
      number = self.currentRow()

      # Modify entry if it is not the first row
      if number == 0:

         pass

      else:

         item = self.item(number)
         item.setFlags(item.flags() | Qt.ItemIsEditable)
         self.editItem(item)

         self.itemChanged.connect(self.onDataChanged)
         

class MainWindow(QMainWindow):

   def __init__(self):
      """
      Creates the main window of the app.

      """

      app = QApplication(sys.argv)
      app.setApplicationName("Note Binder")

      super(MainWindow, self).__init__()

      self.path = os.path.abspath(os.getcwd())

      # Specify a vertical layout
      layout = QVBoxLayout()

      # Add a status bar
      self.status = QStatusBar()
      self.setStatusBar(self.status)

      # Add list widget 
      self.listWidget = myListWidget()

      # Add elements to list
      rows = self.listWidget.getEntries()
      for row in rows:
         self.listWidget.addItem(row[1])

      # Connect function for clicking on elements of the list
      self.listWidget.itemClicked.connect(self.listWidget.clicked)
      self.listWidget.itemDoubleClicked.connect(self.listWidget.doubleClicked)

      layout.addWidget(self.listWidget)
      self.setCentralWidget(self.listWidget)

      # Create toolbar and set icon size
      toolbar = self.addToolBar("Notes")
      toolbar.setIconSize(QSize(24, 24))
      menu = self.menuBar().addMenu("&Notes")

      # Create actions to add, delete and modify notes
      add_note = QAction(QIcon(os.path.join("icons", "add.png")), "Add Note...", self)
      add_note.setStatusTip("Add Note...")
      add_note.triggered.connect(self.listWidget.addNote)
      menu.addAction(add_note)
      toolbar.addAction(add_note)

      del_note = QAction(QIcon(os.path.join("icons", "remove.png")), "Delete Note...", self)
      del_note.setStatusTip("Delete Note...")
      del_note.triggered.connect(self.listWidget.removeNote)
      menu.addAction(del_note)
      toolbar.addAction(del_note)

      chg_note = QAction(QIcon(os.path.join("icons", "change.png")), "Modifiy Selected Note...", self)
      chg_note.setStatusTip("Change Note Name...")
      chg_note.triggered.connect(self.listWidget.changeNote)
      menu.addAction(chg_note)
      toolbar.addAction(chg_note)

      self.setWindowTitle("Note Binder")

      self.show()

      app.exec_()

if __name__ == "__main__":
   
   MainWindow()
   
