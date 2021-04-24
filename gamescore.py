import tkinter as tk
from blunderCheck import blunderCheck
from infiniteAnalysis import infiniteAnalysis

class Gamescore(tk.scrolledtext.ScrolledText):
	def __init__(self, parent, boardPane):
		self.boardPane = boardPane
		tk.scrolledtext.ScrolledText.__init__(self, parent)

		# game score
		self.config(wrap=tk.WORD, padx=10, pady=10, state='disabled', width=10, font=("Tahoma", 14))
		self.tag_configure('curMove', foreground="white", background="red")
		self.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.tag_bind('move', '<Enter>', lambda e: self.boardPane.cursorMove('enter'))
		self.tag_bind('move', '<Leave>', lambda e: self.boardPane.cursorMove('leave'))
		self.bind('<Control-e>', self.boardPane.toggleEngine)
		self.bind('<Control-b>', lambda e: blunderCheck(self.boardPane))
		self.bind('<Right>', lambda e: self.boardPane.move(e, 'forward'))
		self.bind('<Left>', lambda e: self.boardPane.move(e, 'backward'))
		self.bind("<Down>", self.boardPane.selectVariation)
		self.bind("<Up>", self.boardPane.selectVariation)
		self.bind("<Control-o>", self.boardPane.loadGameFile)
		self.bind("<Control-w>", self.boardPane.removeTab)
		
	# emphasize current move in game score
	def updateGameScore(self):
		nodeIdx = self.boardPane.nodes.index(self.boardPane.curNode)
		ranges = self.tag_ranges('move')
		if self.tag_ranges('curMove'):
			self.tag_remove('curMove', 'curMove.first', 'curMove.last')
		if nodeIdx: 
			self.tag_add('curMove', ranges[nodeIdx*2-2], ranges[nodeIdx*2-1])
		# keep the current move visible in the game score
		if self.tag_ranges('curMove'):
			self.see('curMove.first')

	# click on move in gamescore updates board to that move
	def gameScoreClick(self, e):
		moveIndices = []
		# get text indicies of click location
		location = f"@{e.x},{e.y}+1 chars"
		# find the indices of the clicked move tag
		moveTagRange = self.tag_prevrange('move', location)
		# tuple of begin and end indices for all move tags
		ranges = self.tag_ranges('move')
		# convert range to pairs of tuples so they can be compared with moveTagRange
		for x in range(0, len(ranges), 2):
			moveIndices.append((str(ranges[x]), str(ranges[x+1])))
		# set currentNode to the clicked move
		# we add 1 because nodes[0] is the opening position which 
		# is not represented as a move on the game score
		self.boardPane.curNode = self.boardPane.nodes[moveIndices.index(moveTagRange)+1]
		self.boardPane.canvas.printCurrentBoard()
		self.boardPane.printVariations()
		self.updateGameScore()
		if self.boardPane.activeEngine != None:
			infiniteAnalysis(self.boardPane)

	def humanMovetoGameScore(self, move):
		# if the move is already a variation, update board as usual
		if self.boardPane.curNode.has_variation(move):
			self.boardPane.curNode = self.boarPane.curNode.variation(move)
			self.updateGameScore()
		# otherwise, we need to add the variation
		else:
			# breakpoint()
			self.config(state='normal')
			moveranges = self.tag_ranges('move')
			curNodeIndex = self.boardPane.nodes.index(self.boardPane.curNode)
			board = self.boardPane.curNode.board()
			self.boardPane.curNode = self.boardPane.curNode.add_variation(move)
			# if starting a variation, need to open paren before the next move,
			# set mark between parens, and output first move
			moveTxt = f"{self.boardPane.curNode.san()}" 
			if self.boardPane.curNode.starts_variation():
				insertPoint = moveranges[curNodeIndex*2+1]
				moveNo = f"{board.fullmove_number}." if board.turn else f"{board.fullmove_number}..."
				self.tag_remove('curMove', '0.0', 'end')
				# Bug: new variation should go before the next mainline move,
				# not before the sibling variation.
				self.insert(insertPoint, ' ()')
				# put varEnd mark between the ()
				self.mark_set('varEnd', f"{insertPoint}+2 c")
				self.insert('varEnd', moveNo)
				self.insert('varEnd', moveTxt, ('move', 'curMove'))
				# add variation to node list
				self.boardPane.nodes.insert(curNodeIndex+2, self.boardPane.curNode)
			# if continuing a variation, need to add move at mark
			else:
				# breakpoint()
				insertPoint = moveranges[curNodeIndex*2]
				offset = 2
				endOfVar = f"{insertPoint}-{offset} c"
				self.mark_set('varEnd', endOfVar)
				moveNo = f" {board.fullmove_number}." if board.turn else " "
				self.tag_remove('curMove', '0.0', 'end')
				self.insert('varEnd', moveNo)
				self.insert('varEnd', moveTxt, ('move', 'curMove'))
				# add variation to node list
				self.boardPane.nodes.insert(curNodeIndex+1, self.boardPane.curNode)

			self.config(state='disabled')


