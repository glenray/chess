import chess
import chess.pgn
import os
import tkinter as tk
import tkinter.ttk as ttk

class dbSettings(tk.Frame):
	def __init__(self, parent, dbPane):
		tk.Frame.__init__(self, parent)
		self.dbPane = dbPane
		self.config(borderwidth=5, relief='raised', padx=10, pady=10)
		self.setup()

	def setDB(self, e=None):
		dbName = self.dbSelect.get('anchor')
		message = f'{dbName} was selected.\n'
		self.dbPane.messages.insert('end', message)
		self.dbPane.searchForm.database = f'databases/{dbName}'

	def setup(self):
		self.titleLbl = tk.Label(self, text="Select Database", font=('Helvetica', 16)).pack()
		self.dbSelect = tk.Listbox(self)
		self.dbSelect.bind('<<ListboxSelect>>', self.setDB)
		files = os.listdir('databases')
		# get database file names
		for file in files:
			if os.path.splitext(file)[1] == '.db':
				self.dbSelect.insert('end', file)
		self.dbSelect.selection_set(0)
		dbName = self.dbSelect.get(0)
		self.dbPane.searchForm.database = f'databases/{dbName}'
		self.dbSelect.pack()

		self.openPGNBtn = tk.Button(self, text="Open PGN File", command=self.dbPane.resultTree.pgn2Tree)
		self.openPGNBtn.pack()

		
