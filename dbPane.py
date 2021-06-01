import tkinter as tk
import tkinter.ttk as ttk

from dbResults import dbResults
from dbSearch import dbSearch
from dbSettings import dbSettings
import strings as sql

class dbPane(tk.Frame):
	def __init__(self, parent):
		tk.Frame.__init__(self, parent.notebook)
		self.gui = parent
		self.setup()

	def setup(self):
		# Insert pane into the parent notebook
		self.gui.notebook.add(self, text="Database")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)
		
		# search frame which has its own entry and button widgets
		self.searchFrame = tk.Frame(self)
		self.searchForm = dbSearch(self.searchFrame, self)
		self.messages = tk.Text(self.searchFrame, bg='blue', fg='white', font=('Helvetica', 14), height=11)
		
		self.resultFrame = tk.Frame(self, bg='blue')
		self.resultTree = dbResults(self.resultFrame, self)
		self.resultSB = tk.Scrollbar(self.resultFrame)
		self.resultTree.config(yscrollcommand=self.resultSB.set)
		
		self.settings = dbSettings(self.searchFrame, self)

		self.settings.pack(side='left', fill='both', expand=True)
		self.searchFrame.pack(fill='both', expand=True)
		self.searchForm.pack(side='left', fill='both', expand=True)
		self.messages.pack(side='left', fill='both', expand=True)
		# result frame > result tree view and its scroll bar
		self.resultSB.config(command=self.resultTree.yview)
		self.resultSB.pack(side='right', fill='y')
		self.resultFrame.pack(fill='both', expand=True)
		self.resultTree.pack(side='left', fill='both', expand=True)
		