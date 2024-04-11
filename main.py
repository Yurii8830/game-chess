from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Tuple

# Initialize FastAPI app
app = FastAPI()

# Initialize SQLite database
engine = create_engine('sqlite:///chess_game.db', echo=True)
Base = declarative_base()

# Define database models
class Move(Base):
    __tablename__ = 'moves'

    id = Column(Integer, primary_key=True)
    player = Column(String)
    start = Column(String)
    end = Column(String)
    game_id = Column(Integer, ForeignKey('games.id'))

class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    current_player = Column(String)
    moves = relationship('Move', backref='game')
    game_moves = relationship('GameMove', backref='game')

class GameMove(Base):
    __tablename__ = 'game_moves'

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    move_number = Column(Integer)
    player = Column(String)
    start = Column(String)
    end = Column(String)

Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

# Define Pydantic models for request and response bodies
class MoveRequest(BaseModel):
    player: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    game_id: int

class GameResponse(BaseModel):
    id: int
    current_player: str

# Define abstract base class for chess pieces
class Piece:
    def __init__(self, color):
        self.color = color

    def valid_move(self, start, end, board):
        raise NotImplementedError("Subclass must implement abstract method")

    def serialize(self):
        return str(self)

    def __str__(self):
        raise NotImplementedError("Subclass must implement abstract method")

# Define specific chess piece classes
class King(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        diff_x = abs(start[0] - end[0])
        diff_y = abs(start[1] - end[1])
        if diff_x <= 1 and diff_y <= 1:
            return True

        return False

    def __str__(self):
        return "♚" if self.color == "black" else "♔"

class Rook(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        if start[0] == end[0] or start[1] == end[1]:
            if start[0] == end[0]:
                step = 1 if end[1] > start[1] else -1
                for col in range(start[1] + step, end[1], step):
                    if board[start[0]][col] is not None:
                        return False
            else:
                step = 1 if end[0] > start[0] else -1
                for row in range(start[0] + step, end[0], step):
                    if board[row][start[1]] is not None:
                        return False
            return True

        return False

    def __str__(self):
        return "♜" if self.color == "black" else "♖"

class Knight(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        if abs(end[0] - start[0]) == 2 and abs(end[1] - start[1]) == 1:
            return True
        elif abs(end[0] - start[0]) == 1 and abs(end[1] - start[1]) == 2:
            return True

        return False

    def __str__(self):
        return "♞" if self.color == "black" else "♘"

class Bishop(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        diff_x = abs(start[0] - end[0])
        diff_y = abs(start[1] - end[1])
        if diff_x == diff_y:
            return True

        return False

    def __str__(self):
        return "♝" if self.color == "black" else "♗"

class Queen(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        diff_x = abs(start[0] - end[0])
        diff_y = abs(start[1] - end[1])
        if diff_x == diff_y or start[0] == end[0] or start[1] == end[1]:
            return True

        return False

    def __str__(self):
        return "♛" if self.color == "black" else "♕"

class Pawn(Piece):
    def valid_move(self, start, end, board):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        diff_x = abs(start[0] - end[0])
        diff_y = abs(start[1] - end[1])
        if diff_x == 1 and diff_y == 0:
            return True

        return False

    def __str__(self):
        return "♟" if self.color == "black" else "♙"

# Define the chess board class
class Board:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_board()

    def initialize_board(self):
        self.board[0] = [Rook("black"), Knight("black"), Bishop("black"), Queen("black"), King("black"),
                         Bishop("black"), Knight("black"), Rook("black")]
        self.board[1] = [Pawn("black") for _ in range(8)]
        self.board[6] = [Pawn("white") for _ in range(8)]
        self.board[7] = [Rook("white"), Knight("white"), Bishop("white"), Queen("white"), King("white"),
                         Bishop("white"), Knight("white"), Rook("white")]

    def is_valid_move(self, start, end):
        if not (0 <= end[0] < 8 and 0 <= end[1] < 8):
            return False

        piece = self.board[start[0]][start[1]]
        if not piece:
            return False

        return piece.valid_move(start, end, self.board)

    def move_piece(self, start, end):
        piece = self.board[start[0]][start[1]]
        self.board[start[0]][start[1]] = None
        self.board[end[0]][end[1]] = piece

    def serialize_board(self):
        serialized_board = []
        for i, row in enumerate(self.board):
            serialized_row = [str(7 - i)] + [str(j) + str(piece) if piece is not None else ' ' + str(j) for j, piece in
                                             enumerate(row)]
            serialized_board.append(serialized_row)
        serialized_board.append([' ', '0', '1', '2', '3', '4', '5', '6', '7'])
        return serialized_board

# Initialize the game
game = Game(current_player="white")
board = Board()

# Define FastAPI routes
@app.post("/start_game/")
def start_game():
    new_game = Game(current_player="white")
    session.add(new_game)
    session.commit()
    return {"message": "Game started", "game_id": new_game.id}

@app.post("/move/")
def move(move: MoveRequest):
    game = session.query(Game).filter_by(id=move.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.current_player != move.player:
        raise HTTPException(status_code=400, detail="It's not your turn")

    if not board.is_valid_move(move.start, move.end):
        raise HTTPException(status_code=400, detail="Invalid move")

    board.move_piece(move.start, move.end)
    game.current_player = "black" if game.current_player == "white" else "white"
    session.commit()

    # Save the move to the database
    move_number = len(game.game_moves) + 1
    game_move = GameMove(game_id=game.id, move_number=move_number, player=move.player, start=str(move.start),
                         end=str(move.end))
    session.add(game_move)
    session.commit()

    return {"message": "Move made", "game_id": game.id, "current_player": game.current_player}

@app.post("/end_game/")
def end_game(game_id: int):
    game = session.query(Game).filter_by(id=game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    session.delete(game)
    session.commit()
    return {"message": "Game ended"}

@app.get("/get_board/{game_id}")
def get_board(game_id: int):
    game = session.query(Game).filter_by(id=game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    serialized_board = []
    for row in board.board:
        serialized_row = []
        for piece in row:
            serialized_row.append(piece.serialize() if piece is not None else None)
        serialized_board.append(serialized_row)

    return serialized_board

@app.get("/initial_board/")
def get_initial_board():
    initial_board = board.serialize_board()
    return initial_board

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
