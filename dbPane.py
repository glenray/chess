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
		self.searchFrame = tk.Frame(self, bg='red')
		self.resultFrame = tk.Frame(self, bg='blue')
		self.myresults = dbResults(self.resultFrame, self)
		self.mysearch = dbSearch(self.searchFrame, self)

		self.searchFrame.pack(fill='both', expand=True)
		self.resultFrame.pack(fill='both', expand=True)
		# self.textWidget.pack(side='left', fill='x', expand=True)
		self.myresults.pack(side='left', fill='both', expand=True)
		self.mysearch.pack(side='left', fill='both', expand=True)
