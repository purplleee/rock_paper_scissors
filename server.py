import socket
import threading
import random

class RockPaperScissorsServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.clients = []
        self.moves = {}

    def start(self):
        self.server_socket.listen(2)
        print(f"Server listening on {self.host}:{self.port}")
        
        while len(self.clients) < 2:
            client_socket, address = self.server_socket.accept()
            print(f"Connection from {address}")
            self.clients.append(client_socket)
            
            # Send choice instructions to client
            choice_instructions = (
                "Choose your move:\n"
                "1 - Rock\n"
                "2 - Paper\n"
                "3 - Scissors\n"
                "Enter your choice (1/2/3): "
            )
            client_socket.send(choice_instructions.encode())
        
        # Start game session with connected clients
        self.start_game_session()

    def start_game_session(self):
        # Receive moves from both clients
        for i, client in enumerate(self.clients):
            try:
                move = client.recv(1024).decode().strip()
                if not self.validate_move(move):
                    client.send("Invalid move. Please choose 1, 2, or 3.".encode())
                    return
                self.moves[f"Player{i+1}"] = move
            except Exception as e:
                print(f"Error receiving move from Player{i+1}: {e}")
                return
        
        # Determine winner
        result = self.determine_winner(
            self.moves["Player1"], 
            self.moves["Player2"]
        )
        
        # Send results to both clients
        for client in self.clients:
            client.send(result.encode())
        
        # Close connections
        for client in self.clients:
            client.close()

    def validate_move(self, move):
        # Check if move is a valid number between 1 and 3
        return move in ['1', '2', '3']

    def determine_winner(self, move1, move2):
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
            return f"It's a tie! Both players chose {move1_word}"
        
        # All winning scenarios
        winning_combos = {
            '1': '3',  # Rock beats Scissors
            '2': '1',  # Paper beats Rock
            '3': '2'   # Scissors beats Paper
        }
        
        if winning_combos[move1] == move2:
            return f"Player 1 wins! {move1_word} beats {move2_word}"
        else:
            return f"Player 2 wins! {move2_word} beats {move1_word}"

def main():
    server = RockPaperScissorsServer()
    server.start()

if __name__ == "__main__":
    main()

