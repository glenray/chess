import tkinter as tk
import threading, random, string
import chess
import chess.engine
import chess.pgn

# used as the header for infinite analysis output
analysisHeader = '''Score	Depth	Nodes		NPS		Time
{score}	{depth}	{nodes:,}		{nps:,}		{time}
{pvString}'''

class Analysis_text(tk.Text):
	def __init__(self, parent, boardPane):
		self.boardPane = boardPane
		tk.Text.__init__(self, parent)
		self.configure(height=10)

		self.config(wrap=tk.WORD)
		self.bind('<FocusIn>', lambda e: self.boardPane.pWindow.focus())
		self.bind("<Down>", self.boardPane.variations.selectVariation)
		self.bind("<Up>", self.boardPane.variations.selectVariation)

class infiniteAnalysis:
	def __init__(self, boardPane):
		self.boardPane = boardPane
		self.spawnEngine()

	# spawn a new engine thread when self.board changes 
	def spawnEngine(self):
		# generate random thread name
		threadName = "".join(random.choice(string.ascii_letters) for _ in range(10))
		self.boardPane.activeEngine = threadName
		threading.Thread(
			target=self.__engine, 
			args=(threadName,), 
			daemon=True).start()

	# Engine analyzing the current board
	# This is always run in a separate thread by self.spawnEngine()
	# tName str name of the thread
	# The thread running this engine will quit if it is no longer named
	# as the active engine in self.boardPane.activeEngine
	def __engine(self, tName):
		print(f"Engine {tName} On.")
		board = self.boardPane.curNode.board()
		engine = chess.engine.SimpleEngine.popen_uci("C:/Users/Glen/Documents/python/stockfish/bin/stockfish_20090216_x64_bmi2.exe")
		with engine.analysis(board) as analysis:
			for info in analysis:
				# if this is no longer the active engine, quit thread
				if self.boardPane.activeEngine != tName:
					print(f"Engine {tName} Off.")
					break

				pv = info.get('pv')
				if pv != None and (len(pv) > 5 or info.get("score").is_mate()):
					output = analysisHeader.format(
						score = info.get("score").white(),
						depth = info.get('depth'),
						nps = info.get('nps'),
						nodes = info.get('nodes'),
						time = info.get('time'),
						pvString = board.variation_san(pv)	
					)
					self.boardPane.analysis.delete('0.0', 'end')
					self.boardPane.analysis.insert("0.1", output)
		engine.quit()
