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
		self.configure(height=10, wrap=tk.WORD)
		# prevent text box from taking focus and blocking keyboard events
		self.bind('<FocusIn>', lambda e: self.boardPane.focus())

class infiniteAnalysis:
	def __init__(self, boardPane):
		self.boardPane = boardPane
		self.enginePath = "C:/Users/Glen/Documents/python/stockfish/bin/stockfish_20090216_x64_bmi2.exe"
		self.spawnEngine()

	def spawnEngine(self):
		# spawn a new engine thread when self.board changes 
		# generate random thread name
		threadName = "".join(random.choice(string.ascii_letters) for _ in range(10))
		self.boardPane.activeEngine = threadName
		threading.Thread(
			target=self.__engine, 
			args=(threadName,), 
			daemon=True).start()

	def __engine(self, tName):
		'''
		Engine analyzing the current board
		This is always run in a separate thread by self.spawnEngine()
		tName str name of the thread
		The thread running this engine will quit if it is no longer named
		as the active engine in self.boardPane.activeEngine
		'''
		print(f"Engine {tName} On.")
		board = self.boardPane.curNode.board()
		engine = chess.engine.SimpleEngine.popen_uci(self.enginePath)
		with engine.analysis(board) as analysis:
			for info in analysis:
				# if this is no longer the active engine, kill this thread
				try:
					if self.boardPane.activeEngine != tName:
						print(f"Engine {tName} Off.")
						break
				# if the boardPane was closed by the user
				except:
					print(f"Board closed while analysis active")
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
					# if the board pane has been closed by the user, catch the exception and quit
					try:
						self.boardPane.analysis.delete('0.0', 'end')
						self.boardPane.analysis.insert("0.1", output)
					except:
						print(f"Board closed while analysis active")
						print(f"Engine {tName} Off.")
						break
		engine.quit()
