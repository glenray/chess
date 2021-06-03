import tkinter as tk
from formRecipies import recipies

class dbSearch(tk.Frame):
	'''
	The search box
	'''
	def __init__(self, parent, dbPane):
		tk.Frame.__init__(self, parent)
		self.dbPane = dbPane
		self.config(borderwidth=5, relief='raised', padx=10, pady=10)
		# self.formFactory(recipies['getPlayerGames'])
		self.formFactory(recipies['getGamesBtwPlayers'])
		self.sourcePath = None

	def execSearch(self):
		data, i = {}, 0
		for param in self.formRecipe['params']:
			data[param] = f'{self.widgets[i]["widget"].get()}*'
			i+=1
		sql = self.formRecipe['sql']
		self.dbPane.dbResults.getResults(self.sourcePath, sql, data)

	def formFactory(self, formRecipe):
		'''
		Create a search form based on data in formRecipe.
		'''
		self.formRecipe = formRecipe
		self.widgets = []
		paramCount = len(formRecipe['params'])
		for row in range(0, paramCount+2):
			self.rowconfigure(row, pad=20)
		# create widgets
		titleLbl = tk.Label(self, 
			text=formRecipe['title'], 
			font=('Helvetica', 16))
		for param in formRecipe['params']:
			self.widgets.append({
				'label': tk.Label(self, text=formRecipe['params'][param]),
				'widget' : tk.Entry(self)
				})
		self.searchBtn = tk.Button(self, text='Search', command=self.execSearch)
		# place widgets on grid
		titleLbl.grid(row=0, column=0, columnspan=2)
		i=1	#The Label and Entry Widget pairs start on row 1
		for widgetRow in self.widgets:
			widgetRow['label'].grid(row=i, column=0)
			widgetRow['widget'].grid(row=i, column=1)
			i+=1
		self.searchBtn.grid(row=i, column=0)

class pgnHandler(tk.Frame):
	def __init__(self, parent, dbPane):
		tk.Frame.__init__(self, parent)
		self.dbPane = dbPane
		self.config(borderwidth=5, relief='raised', padx=10, pady=10)
		self.setup()

	def setup(self):
		titleLbl = tk.Label(self, 
			text='PGN Handler', 
			font=('Helvetica', 16))

		getGames_btn = tk.Button(self,
			text='Get Games',
			command= lambda: self.dbPane.dbResults.pgn2Tree(self.dbPane.searchForm.sourcePath))

		titleLbl.grid(row=0, column=0)
		getGames_btn.grid(row=1, column=0)
