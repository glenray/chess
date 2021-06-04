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
		self.sourceName = tk.StringVar(self.dbPane, 'Source: None')
		self.setup()

	def setDB(self, e=None):
		dbName = self.dbSelect.get('anchor')
		message = f'{dbName} was selected.\n'
		self.dbPane.messages.insert('end', message)
		self.dbPane.searchForm.database = f'databases/{dbName}'

	def setup(self):
		self.titleLbl = tk.Label(self, 
			text="Select Souce", 
			font=('Helvetica', 16),
			pady=20
			).pack()

		self.openPGNBtn = tk.Button(
			self, 
			text="Open Source File", 
			command=self.openFile,
			pady=20
			).pack()

		self.source_lbl = tk.Label(self,
			textvariable=self.sourceName,
			font=('Helvetica', 10)
			).pack(pady=20, side='top', anchor='w')

	def openFile(self):
		''' 
		Set the current game source file: .db or .pgn 
		'''
		filename = tk.filedialog.askopenfilename(
			initialdir='pgn', 
			filetypes=[('Game Sources', ('.pgn .db'))],
			title= 'Open PGN File'
		)
		if filename:
			self.dbPane.searchForm.sourcePath = filename
			self.sourceName.set(f'Source: {os.path.basename(filename)}')
			ext = os.path.splitext(filename)[1]
			if ext == '.db':
				self.dbPane.searchForm.lift()
				self.dbPane.dbResults.offsets = None
			elif ext == '.pgn':
				self.dbPane.pgnHandler.lift()
				self.dbPane.dbResults.games = None
			else:
				self.dbPane.messages.insert('end', f'\nError: selected file must have .db or .pgn extension.')
				return False
			self.dbPane.dbResults.resetTree()
			self.dbPane.messages.delete('1.0', 'end')
