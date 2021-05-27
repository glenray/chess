import tkinter as tk

class dbSearch(tk.Frame):
	def __init__(self, parent, dbPane):
		tk.Frame.__init__(self, parent)
		self.dbPane = dbPane
		self.setup()

	def setup(self):
		self.rowconfigure(0, pad=20)
		self.rowconfigure(1, pad=20)
		self.rowconfigure(2, pad=20)
		# create widgets
		self.p1_label = tk.Label(self, text="Player 1")
		self.p2_label = tk.Label(self, text="Player 2")
		self.p1_entry = tk.Entry(self)
		self.p2_entry = tk.Entry(self)
		self.searchBtn = tk.Button(self, text='Search', command = self.execSearch)
		# place widgets in grid
		self.p1_label.grid(row=0, column=0)
		self.p1_entry.grid(row=0, column=1)
		self.p2_label.grid(row=1, column=0)
		self.p2_entry.grid(row=1, column=1)
		self.searchBtn.grid(row=2, column=0, columnspan=2)

	def execSearch(self):
		self.dbPane.myresults.getData(self.p1_entry.get(), self.p2_entry.get())