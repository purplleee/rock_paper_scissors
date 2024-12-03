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
        try:
            while True:
                print("Waiting for players to connect...")
                self.reset_game_state()
                self.wait_for_players()
                
                # If fewer than 2 players, continue waiting
                if len(self.clients) < 2:
                    print("Not enough players.")
                    continue
                
                # Play game series
                self.play_game_series()
                
                # Break the loop after game series
                break
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Cleanup server socket
            try:
                self.server_socket.close()
            except:
                pass

    def reset_game_state(self):
        # Close existing client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        self.clients.clear()
        self.moves.clear()
        self.scores = {"Player1": 0, "Player2": 0}
        self.round = 0

    def wait_for_players(self):
        self.server_socket.listen(2)
        print(f"Server listening on {self.host}:{self.port}")
        
        # Set a timeout for waiting for players
        self.server_socket.settimeout(120)  # 2 minutes timeout
        
        try:
            while len(self.clients) < 2:
                try:
                    client_socket, address = self.server_socket.accept()
                    print(f"Connection from {address}")
                    self.clients.append(client_socket)
                    
                    # Send initial game instructions (only once)
                    welcome_msg = (
                        "Welcome to Rock-Paper-Scissors Multiplayer!\n"
                        "Choose your move:\n"
                        "1 - Rock\n"
                        "2 - Paper\n"
                        "3 - Scissors\n"
                    )
                    client_socket.send(welcome_msg.encode())
                    
                    # If two players have joined, send ready message
                    if len(self.clients) == 2:
                        ready_msg = "Both players connected! Let's start the game!\n"
                        for client in self.clients:
                            client.send(ready_msg.encode())
                
                except socket.timeout:
                    print("Timeout waiting for players.")
                    return
        except Exception as e:
            print(f"Error accepting connections: {e}")

    def play_game_series(self):
        try:
            while self.round < self.MAX_ROUNDS:
                self.round += 1
                print(f"Starting Round {self.round}")
                
                # Reset moves for this round
                self.moves.clear()
                
                # Send round start message
                round_start_msg = f"\n--- Round {self.round} ---\n"
                for client in self.clients:
                    client.send(round_start_msg.encode())
                
                # Receive moves from both clients
                self.play_single_round()
                
                # Check if series is over
                if max(self.scores.values()) >= 2:
                    break
            
            # Send final game result
            self.get_series_winner()
        
        except Exception as e:
            print(f"Error during game series: {e}")

    def play_single_round(self):
        for i, client in enumerate(self.clients):
            try:
                # Prompt for move (simplified prompt)
                move_prompt = f"Player {i+1}, enter your choice (1/2/3): "
                client.send(move_prompt.encode())
                
                # Set a timeout for receiving move
                client.settimeout(30)  # 30 seconds to make a move
                move = client.recv(1024).decode().strip()
                
                # Validate move
                if not self.validate_move(move):
                    client.send("Invalid move. Please choose 1, 2, or 3.".encode())
                    return
                
                self.moves[f"Player{i+1}"] = move
            except socket.timeout:
                print(f"Player{i+1} took too long to move")
                return
            except Exception as e:
                print(f"Error receiving move from Player{i+1}: {e}")
                return
        
        # Determine round winner
        self.determine_round_winner(
            self.moves["Player1"], 
            self.moves["Player2"]
        )

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
            # Personalized tie message for each player
            for client in self.clients:
                client.send(f"Round {self.round} Tie! Both players chose {move1_word}".encode())
            return
        
        # All winning scenarios
        winning_combos = {
            '1': '3',  # Rock beats Scissors
            '2': '1',  # Paper beats Rock
            '3': '2'   # Scissors beats Paper
        }
        
        if winning_combos[move1] == move2:
            # Player 1 wins
            self.scores["Player1"] += 1
            # Send personalized messages to each player
            self.clients[0].send(
                (f"Round {self.round} - You won! {move1_word} beats {move2_word}\n"
                 f"Current Score - You: {self.scores['Player1']}, Opponent: {self.scores['Player2']}").encode()
            )
            self.clients[1].send(
                (f"Round {self.round} - You lost! {move2_word} is beaten by {move1_word}\n"
                 f"Current Score - You: {self.scores['Player2']}, Opponent: {self.scores['Player1']}").encode()
            )
        else:
            # Player 2 wins
            self.scores["Player2"] += 1
            # Send personalized messages to each player
            self.clients[0].send(
                (f"Round {self.round} - You lost! {move1_word} is beaten by {move2_word}\n"
                 f"Current Score - You: {self.scores['Player1']}, Opponent: {self.scores['Player2']}").encode()
            )
            self.clients[1].send(
                (f"Round {self.round} - You won! {move2_word} beats {move1_word}\n"
                 f"Current Score - You: {self.scores['Player2']}, Opponent: {self.scores['Player1']}").encode()
            )

    def get_series_winner(self):
        if self.scores["Player1"] > self.scores["Player2"]:
            # Send personalized final result
            self.clients[0].send(f"Game Over! You won the series {self.scores['Player1']}-{self.scores['Player2']}".encode())
            self.clients[1].send(f"Game Over! You lost the series {self.scores['Player1']}-{self.scores['Player2']}".encode())
        elif self.scores["Player2"] > self.scores["Player1"]:
            # Send personalized final result
            self.clients[0].send(f"Game Over! You lost the series {self.scores['Player2']}-{self.scores['Player1']}".encode())
            self.clients[1].send(f"Game Over! You won the series {self.scores['Player2']}-{self.scores['Player1']}".encode())
        else:
            # Send tie message to both
            for client in self.clients:
                client.send("Game Over! The series is a tie!".encode())

def main():
    server = RockPaperScissorsServer()
    server.start()

if __name__ == "__main__":
    main()