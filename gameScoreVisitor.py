import pdb
# pdb.set_trace()
import chess
import chess.pgn
import copy

class gameScoreVisitor(chess.pgn.BaseVisitor):
	def __init__(self, gui):
# this will go
		self.output = ""
		self.startsVariation = False
		self.endsVariation = False
		self.gui = gui
		self.currentNode = self.gui.game
		self.varStack = []
		self.nodes = []

	def end_headers(self):
		gs = self.gui.gameScore
		gs.config(state='normal')
		g=self.gui.game.headers
		gameTitle = f"{g['White']} ({g['WhiteElo']}) vs. {g['Black']} ({g['BlackElo']})"
		eco = f"\nECO: {g['ECO']}\n\n"
		gs.insert("end", gameTitle)
		gs.insert("end", eco)

	def visit_header(self, tagname, tagvalue):
		pass
		# tags = ('BLACK', 'WHite', 'eco', 'event', "whiteelo", 'blackelo')
		# if tagname.casefold() in (x.casefold() for x in tags):
		# 	self.output += f"{tagname}: {tagvalue}\n"

	def visit_move(self, board, move):
		# pdb.set_trace()
		gs = self.gui.gameScore
		moveNo = f"{board.fullmove_number}." if board.turn else ""
		if self.endsVariation:
			self.endsVariation = False
			self.currentNode = self.varStack.pop()
			gs.insert("end", ")")

		if self.startsVariation:
			self.startsVariation = False
			if board.turn == False:
				moveNo = f"{board.fullmove_number}..."
			self.varStack.append(self.currentNode)
			self.currentNode = self.currentNode.parent
			gs.insert("end", "(")

		self.currentNode = self.currentNode.variation(move)
		self.nodes.append(self.currentNode)
		gs.insert('end', f"{moveNo}")
		# tag each move
		gs.insert('end', f"{board.san(move)} ", ('move',))

	def begin_variation(self):
		self.startsVariation = True

	def end_variation(self):
		self.endsVariation = True

	def visit_comment(self, comment):
		c = f"{{{comment}}} ".replace('\n', ' ')
		self.gui.gameScore.insert('end', c)

	def result(self):
		return self.nodes
