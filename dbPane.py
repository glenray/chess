import tkinter as tk
import tkinter.ttk as ttk

from dbResults import dbResults
from dbSearch import dbSearch, pgnHandler
from dbSettings import dbSettings
import strings as sql

class dbPane(tk.Frame):
	'''	dbPane Structure:
	searchFrame
		settings
		searchForm
		messages
	resultFrame
		dbResults & dbResultsSB
	'''
	def __init__(self, parent):
		tk.Frame.__init__(self, parent.notebook)
		self.gui = parent
		self.setup()

	def setup(self):
		# Insert pane into the parent notebook
		self.gui.notebook.add(self, text="Database")
		self.gui.notebook.select(self.gui.notebook.index('end')-1)
		# create child widgets
		self.searchFrame = tk.Frame(self)
		self.searchForm = dbSearch(self.searchFrame, self)
		self.pgnHandler = pgnHandler(self.searchFrame, self)
		self.messages = tk.Text(self.searchFrame, 
			bg='blue', 
			fg='white', 
			font=('Helvetica', 14), 
			height=1,
			width=20)
		self.resultFrame = tk.Frame(self, bg='blue')
		self.dbResults = dbResults(self.resultFrame, self)
		self.dbResultsSB = tk.Scrollbar(self.resultFrame)
		self.settings = dbSettings(self.searchFrame, self)
		# configure widgets
		self.dbResults.config(yscrollcommand=self.dbResultsSB.set)
		self.dbResultsSB.config(command=self.dbResults.yview)
		# place searchFrame children in grid
		self.searchFrame.columnconfigure(0, weight=1)
		self.searchFrame.columnconfigure(1, weight=1)
		self.searchFrame.columnconfigure(2, weight=3)
		self.searchFrame.rowconfigure(0, weight=1)
		self.settings.grid(column=0, row=0, sticky='nsew')
		self.searchForm.grid(column=1, row=0, sticky='nsew')
		self.pgnHandler.grid(column=1, row=0, sticky='nsew')
		self.messages.grid(column=2, row=0, sticky='nsew')

		# pack other widgets
		self.searchFrame.pack(fill='both', expand=True)
		self.dbResultsSB.pack(side='right', fill='y')
		self.resultFrame.pack(fill='both', expand=True)
		self.dbResults.pack(side='left', fill='both', expand=True)
		