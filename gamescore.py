import tkinter as tk
from blunderCheck import blunderCheck
from analysis import infiniteAnalysis

class Gamescore(tk.scrolledtext.ScrolledText):
	def __init__(self, parent, boardPane):
		self.boardPane = boardPane
		tk.scrolledtext.ScrolledText.__init__(self, parent)
		self.config(wrap=tk.WORD, padx=10, pady=10, 
			state='disabled', width=10, font=("Tahoma", 14))
		self.tag_configure('curMove', foreground="white", background="red")
		self.tag_bind('move', '<Button-1>', self.gameScoreClick)
		self.tag_bind('move', '<Enter>', lambda e: self.cursorMove('enter'))
		self.tag_bind('move', '<Leave>', lambda e: self.cursorMove('leave'))
		# prevent gamescore from taking focus and blocking keyboard events
		self.bind('<FocusIn>', lambda e: self.boardPane.focus())

	def cursorMove(self, status):
		# changes the cursor when hovering over a move in the game score
		if status == 'leave':
			self.config(cursor='')
		elif status == 'enter':
			self.config(cursor='hand2')

	def updateGameScore(self):
		# emphasize current move in game score
		nodeIdx = self.boardPane.nodes.index(self.boardPane.curNode)
		ranges = self.tag_ranges('move')
		if self.tag_ranges('curMove'):
			self.tag_remove('curMove', 'curMove.first', 'curMove.last')
		if nodeIdx: 
			self.tag_add('curMove', ranges[nodeIdx*2-2], ranges[nodeIdx*2-1])
		# keep the current move visible in the game score
		if self.tag_ranges('curMove'):
			self.see('curMove.first')

	def gameScoreClick(self, e):
		# click on move in gamescore updates board to that move
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
		self.boardPane.variations.printVariations()
		self.updateGameScore()
		if self.boardPane.activeEngine != None:
			infiniteAnalysis(self.boardPane)

	def getInsertPoint(self, node):
		offset = 0
		moveranges = self.tag_ranges('move')
		if len(node.variations) == 0:
			myNode = node
		else:
			myNode = node.variations[-1]

		# new variation goes behind existing sub variations
		if len(node.variations)>1:
			myNode = myNode.end()
			offset += 3

		nodeIdx = self.boardPane.nodes.index(myNode)-1

		begin, end = moveranges[(nodeIdx*2)], moveranges[(nodeIdx*2)+1]
		commentLen = len(myNode.comment)
		if commentLen>0:
			offset += 4
		end = f"{end}+{str(commentLen+offset)} chars"
		return end, nodeIdx

	def humanMovetoGameScore(self, move):
		# if the move is already a variation, update board as usual
		if self.boardPane.curNode.has_variation(move):
			self.boardPane.curNode = self.boardPane.curNode.variation(move)
			self.updateGameScore()
		# otherwise, we need to add the variation
		else:
			# breakpoint()
			insertPoint, curNodeIndex = self.getInsertPoint(self.boardPane.curNode)
			board = self.boardPane.curNode.board()
			self.boardPane.curNode = self.boardPane.curNode.add_variation(move)
			moveTxt = f"{self.boardPane.curNode.san()}" 
			moveNo = f"{board.fullmove_number}." if board.turn else f"{board.fullmove_number}..."
			self.tag_remove('curMove', '0.0', 'end')
			self.boardPane.nodes.insert(curNodeIndex+2, self.boardPane.curNode)
			self.config(state='normal')
			self.mark_set('varEnd', insertPoint)
			if self.boardPane.curNode.starts_variation():
				self.insert('varEnd', ' (')
			self.insert('varEnd', f' {moveNo}')
			self.insert('varEnd', moveTxt, ('move', 'curMove'))
			if self.boardPane.curNode.starts_variation():
				self.insert('varEnd', ')')
			self.config(state='disabled')

	def outputMove(self, board, move, currentNode, location='end'):
		# breakpoint()
		moveNo = f"{board.fullmove_number}." if board.turn else ""
		# black moves separated from its white counterpart by comment
		# or variation will have move number and elipses pre-pended.
		isBlkTurn = board.turn == False
		isMoveAfterComment = len(currentNode.parent.comment) > 0
		isMoveAfterVar = ((currentNode.parent.parent != None)  
			and (len(currentNode.parent.parent.variations)>1)
			and (board.turn == False))
		if isBlkTurn and (isMoveAfterComment or isMoveAfterVar):
			moveNo = f"{board.fullmove_number}..."

		self.insert(location, f"{moveNo}")
		# tag each move
		self.insert(location, f"{board.san(move)}", ('move',), " ")


	def outputHeaders(self):
		self.config(state='normal')
		self.delete('1.0', 'end')
		g=self.boardPane.game.headers
		whiteElo = f" ({g['WhiteElo']})" if 'WhiteElo' in g else ''
		blackElo = f" ({g['BlackElo']})" if 'BlackElo' in g else ''
		gameTitle = f"{g['White']}{whiteElo} vs. {g['Black']}{blackElo}"
		eco = f"\nECO: {g['ECO']}\n\n" if 'ECO' in g else '\n\n'
		self.insert("end", gameTitle)
		self.insert("end", eco)