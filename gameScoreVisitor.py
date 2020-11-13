from chess.pgn import BaseVisitor
import pdb

'''
Called to populate gui.gameScore text widget with the game score,
including all variations and comments.
'''
class gameScoreVisitor(BaseVisitor):
	def __init__(self, gui):
		# pdb.set_trace()
		self.startsVariation = False
		self.endsVariation = False
		self.gui = gui
		self.currentNode = self.gui.game
		# at the start of a new variation, the current node is pushed
		# to the varStack and popped off when the new variation finishes.
		self.varStack = []
		# the first node is the root, i.e. start position
		self.gui.nodes = [self.currentNode]


	def end_headers(self):
		gs = self.gui.gameScore
		gs.config(state='normal')
		self.gui.gameScore.delete('1.0', 'end')
		g=self.gui.game.headers
		whiteElo = f" ({g['WhiteElo']})" if 'WhiteElo' in g else ''
		blackElo = f" ({g['BlackElo']})" if 'BlackElo' in g else ''
		gameTitle = f"{g['White']}{whiteElo} vs. {g['Black']}{blackElo}"
		eco = f"\nECO: {g['ECO']}\n\n" if 'ECO' in g else '\n\n'
		gs.insert("end", gameTitle)
		gs.insert("end", eco)

	def visit_move(self, board, move):
		gs = self.gui.gameScore
		moveNo = f"{board.fullmove_number}." if board.turn else ""
		if self.endsVariation:
			self.endsVariation = False
			self.currentNode = self.varStack.pop()
			# delete last space after last move in variation
			gs.delete('end-2 chars')
			gs.insert("end", ") ")

		if self.startsVariation:
			self.startsVariation = False
			if board.turn == False:
				moveNo = f"{board.fullmove_number}..."
			self.varStack.append(self.currentNode)
			self.currentNode = self.currentNode.parent
			gs.insert("end", "(")

		self.currentNode = self.currentNode.variation(move)
		self.gui.nodes.append(self.currentNode)
		gs.insert('end', f"{moveNo}")
		# tag each move
		gs.insert('end', f"{board.san(move)}", ('move',))
		gs.insert('end', " ")

	def begin_variation(self):
		self.startsVariation = True

	def end_variation(self):
		self.endsVariation = True

	def visit_comment(self, comment):
		c = f"{{{comment}}} ".replace('\n', ' ')
		self.gui.gameScore.insert('end', c)

	def result(self):
		self.gui.gameScore.config(state='disabled')
		self.gui.curNode = self.gui.nodes[0]
