import socket
import threading
import time

class RockPaperScissorsServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.clients = []
        self.moves = {}
        self.scores = {"Player1": 0, "Player2": 0}
        self.round = 0
        self.MAX_ROUNDS = 3  # Best of 3 rounds

    def start(self):
        self.server_socket.listen(2)
        print(f"Server listening on {self.host}:{self.port}")
        
        # Set a timeout for waiting for players
        self.server_socket.settimeout(60)  # 60 seconds timeout
        
        try:
            while len(self.clients) < 2:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"Connection from {address}")
                    self.clients.append(client_socket)
                    
                    # Send choice instructions to client
                    choice_instructions = (
                        "Welcome to Rock-Paper-Scissors!\n"
                        "Choose your move:\n"
                        "1 - Rock\n"
                        "2 - Paper\n"
                        "3 - Scissors\n"
                        "Enter your choice (1/2/3): "
                    )
                    client_socket.send(choice_instructions.encode())
                except socket.timeout:
                    print("Timeout waiting for players. Closing server.")
                    return
        except Exception as e:
            print(f"Error accepting connections: {e}")
            return

        # Start game session with connected clients
        self.play_game_series()

    def play_game_series(self):
        try:
            while self.round < self.MAX_ROUNDS:
                self.round += 1
                print(f"Starting Round {self.round}")
                
                # Reset moves for this round
                self.moves.clear()
                
                # Receive moves from both clients
                round_results = self.play_single_round()
                
                # Send round summary to both clients
                for client in self.clients:
                    client.send(round_results.encode())
                
                # Check if series is over
                if max(self.scores.values()) >= 2:
                    break
            
            # Send final game result
            final_result = self.get_series_winner()
            for client in self.clients:
                client.send(final_result.encode())
        
        except Exception as e:
            print(f"Error during game series: {e}")
        finally:
            # Close connections
            for client in self.clients:
                client.close()

    def play_single_round(self):
        for i, client in enumerate(self.clients):
            try:
                # Set a timeout for receiving move
                client.settimeout(30)  # 30 seconds to make a move
                move = client.recv(1024).decode().strip()
                
                # Validate move
                if not self.validate_move(move):
                    client.send("Invalid move. Please choose 1, 2, or 3.".encode())
                    return "Invalid move detected. Round cancelled."
                
                self.moves[f"Player{i+1}"] = move
            except socket.timeout:
                print(f"Player{i+1} took too long to move")
                return f"Player{i+1} timed out. Round cancelled."
            except Exception as e:
                print(f"Error receiving move from Player{i+1}: {e}")
                return f"Error receiving move from Player{i+1}."
        
        # Determine round winner
        result = self.determine_round_winner(
            self.moves["Player1"], 
            self.moves["Player2"]
        )
        return result

    def validate_move(self, move):
        # Check if move is a valid number between 1 and 3
        return move in ['1', '2', '3']

    def determine_round_winner(self, move1, move2):
        # Convert numeric moves to rock/paper/scissors
        choices = {
            '1': 'Rock',
            '2': 'Paper', 
            '3': 'Scissors'
        }
        
        # Convert moves to words for readability
        move1_word = choices[move1]
        move2_word = choices[move2]
        
        # Winning combinations
        if move1 == move2:
            round_result = f"Round {self.round} Tie! Both players chose {move1_word}"
            return round_result
        
        # All winning scenarios
        winning_combos = {
            '1': '3',  # Rock beats Scissors
            '2': '1',  # Paper beats Rock
            '3': '2'   # Scissors beats Paper
        }
        
        if winning_combos[move1] == move2:
            self.scores["Player1"] += 1
            round_result = (f"Round {self.round} - Player 1 wins! {move1_word} beats {move2_word}\n"
                            f"Current Score - Player 1: {self.scores['Player1']}, Player 2: {self.scores['Player2']}")
            return round_result
        else:
            self.scores["Player2"] += 1
            round_result = (f"Round {self.round} - Player 2 wins! {move2_word} beats {move1_word}\n"
                            f"Current Score - Player 1: {self.scores['Player1']}, Player 2: {self.scores['Player2']}")
            return round_result

    def get_series_winner(self):
        if self.scores["Player1"] > self.scores["Player2"]:
            return f"Game Over! Player 1 wins the series {self.scores['Player1']}-{self.scores['Player2']}"
        elif self.scores["Player2"] > self.scores["Player1"]:
            return f"Game Over! Player 2 wins the series {self.scores['Player2']}-{self.scores['Player1']}"
        else:
            return "Game Over! The series is a tie!"

def main():
    server = RockPaperScissorsServer()
    server.start()

if __name__ == "__main__":
    main()

