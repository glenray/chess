import tkinter as tk
import tkinter.ttk as ttk

from dbResults import dbResults
from dbSearch import dbSearch
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
		self.mysearch = dbSearch(self.searchFrame, self)
		self.searchFrame.pack(fill='both', expand=True)
		self.mysearch.pack(side='left', fill='both', expand=True)
		# result frame > result tree view and its scroll bar
		self.resultFrame = tk.Frame(self, bg='blue')
		self.resultSB = tk.Scrollbar(self.resultFrame)
		self.resultTree = dbResults(self.resultFrame, self)
		self.resultTree.config(yscrollcommand=self.resultSB.set)
		self.resultSB.config(command=self.resultTree.yview)
		self.resultSB.pack(side='right', fill='y')
		self.resultFrame.pack(fill='both', expand=True)
		self.resultTree.pack(side='left', fill='both', expand=True)
		