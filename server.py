import socket
import threading
import time
import queue
from auth import AuthenticationManager 

class GameSession:
    def __init__(self, player1_info, player2_info):
        self.players = [player1_info[0], player2_info[0]]  # Socket
        self.usernames = [player1_info[1], player2_info[1]]  # Username
        self.auth_manager = AuthenticationManager()
        self.moves = {}
        self.scores = {self.usernames[0]: 0, self.usernames[1]: 0}
        self.round = 0
        self.MAX_ROUNDS = 3
        self.game_over = False

    def collect_moves(self):
        """Collect moves for a single round"""
        self.moves.clear()
        choices = {
            '1': 'Rock', 
            '2': 'Paper', 
            '3': 'Scissors'
        }
        
        for i, player in enumerate(self.players):
            while True:
                try:
                    # Send move prompt with choices using actual username
                    move_prompt = (
                        f"{self.usernames[i]}, choose your move:\n"
                        "1. Rock\n"
                        "2. Paper\n"
                        "3. Scissors\n"
                        "Enter your choice (1/2/3): "
                    )
                    player.send(move_prompt.encode())
                    
                    # Set timeout for move
                    player.settimeout(30)
                    move = player.recv(1024).decode().strip()
                    
                    # Validate move
                    if move not in choices:
                        player.send("Invalid move. Please choose 1, 2, or 3.".encode())
                        continue
                    
                    self.moves[self.usernames[i]] = move
                    break  # Valid move, exit the inner loop
                
                except Exception as e:
                    print(f"Error collecting move from {self.usernames[i]}: {e}")
                    player.send("An error occurred. Please try again.".encode())
        
        return True

    def determine_round_winner(self):
        """Determine winner of a single round"""
        choices = {'1': 'Rock', '2': 'Paper', '3': 'Scissors'}
        move1, move2 = self.moves[self.usernames[0]], self.moves[self.usernames[1]]
        move1_word, move2_word = choices[move1], choices[move2]

        if move1 == move2:
            # Tie
            for player in self.players:
                player.send(f"Round {self.round} Tie! Both players chose {move1_word}".encode())
            return
        
        # All winning scenarios
        winning_combos = {
            '1': '3',  # Rock beats Scissors
            '2': '1',  # Paper beats Rock
            '3': '2'   # Scissors beats Paper
        }
        
        if winning_combos[move1] == move2:
            # Player 1 wins
            self.scores[self.usernames[0]] += 1
            self.players[0].send(
                (f"Round {self.round} - You won! {move1_word} beats {move2_word}\n"
                 f"Current Score - {self.usernames[0]}: {self.scores[self.usernames[0]]}, {self.usernames[1]}: {self.scores[self.usernames[1]]}").encode()
            )
            self.players[1].send(
                (f"Round {self.round} - You lost! {move2_word} is beaten by {move1_word}\n"
                 f"Current Score - {self.usernames[1]}: {self.scores[self.usernames[1]]}, {self.usernames[0]}: {self.scores[self.usernames[0]]}").encode()
            )
        else:
            # Player 2 wins
            self.scores[self.usernames[1]] += 1
            self.players[0].send(
                (f"Round {self.round} - You lost! {move1_word} is beaten by {move2_word}\n"
                 f"Current Score - {self.usernames[0]}: {self.scores[self.usernames[0]]}, {self.usernames[1]}: {self.scores[self.usernames[1]]}").encode()
            )
            self.players[1].send(
                (f"Round {self.round} - You won! {move2_word} beats {move1_word}\n"
                 f"Current Score - {self.usernames[1]}: {self.scores[self.usernames[1]]}, {self.usernames[0]}: {self.scores[self.usernames[0]]}").encode()
            )

    def play_game(self):
        """Run the entire game series"""
        try:
            # Send initial game start message
            game_start_msg = f"Game started! {self.usernames[0]} vs {self.usernames[1]} - Best of 3 rounds."
            for player in self.players:
                player.send(game_start_msg.encode())

            while self.round < self.MAX_ROUNDS:
                # Check if there's an overall winner
                if max(self.scores.values()) >= 2:
                    break
                
                self.round += 1
                print(f"Starting Round {self.round}")
                
                # Send round start message
                round_start_msg = f"\n--- Round {self.round} ---\n"
                for player in self.players:
                    player.send(round_start_msg.encode())
                
                # Collect moves
                if not self.collect_moves():
                    continue
                
                # Determine round winner
                self.determine_round_winner()
            
            # Determine series winner
            self.get_series_winner()
        except Exception as e:
            print(f"Error in game session: {e}")
        finally:
            # Close player connections
            for player in self.players:
                try:
                    player.close()
                except:
                    pass

    def get_series_winner(self):
        """Determine and communicate the overall game winner"""
        if self.scores[self.usernames[0]] > self.scores[self.usernames[1]]:
            self.players[0].send(f"Game Over! You won the series {self.scores[self.usernames[0]]}-{self.scores[self.usernames[1]]}".encode())
            self.players[1].send(f"Game Over! You lost the series {self.scores[self.usernames[0]]}-{self.scores[self.usernames[1]]}".encode())
        elif self.scores[self.usernames[1]] > self.scores[self.usernames[0]]:
            self.players[0].send(f"Game Over! You lost the series {self.scores[self.usernames[1]]}-{self.scores[self.usernames[0]]}".encode())
            self.players[1].send(f"Game Over! You won the series {self.scores[self.usernames[1]]}-{self.scores[self.usernames[0]]}".encode())
        else:
            for player in self.players:
                player.send("Game Over! The series is a tie!".encode())

class RockPaperScissorsServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        
        # Queue for waiting players
        self.waiting_players = queue.Queue()
        
        # Active game sessions
        self.active_sessions = []
        
        # Flag to control server
        self.is_running = True

    def handle_player_connection(self, client_socket):
        # Create authentication manager
        auth_manager = AuthenticationManager()
        
        try:
            # Authentication phase
            client_socket.send("Please login or register (LOGIN/REGISTER username password)".encode())
            
            authenticated = False
            while not authenticated:
                response = client_socket.recv(1024).decode().strip()
                parts = response.split()
                
                if len(parts) != 3:
                    client_socket.send("Invalid format. Use LOGIN/REGISTER username password".encode())
                    continue
                
                action, username, password = parts
                
                if action.upper() == 'REGISTER':
                    if auth_manager.register_user(username, password):
                        client_socket.send("Registration successful!".encode())
                    else:
                        client_socket.send("Username already exists".encode())
                        continue
                
                elif action.upper() == 'LOGIN':
                    if auth_manager.authenticate_user(username, password):
                        authenticated = True
                        client_socket.send("Login successful!".encode())
                    else:
                        client_socket.send("Invalid credentials".encode())
                        continue
                
                else:
                    client_socket.send("Invalid action. Use LOGIN or REGISTER".encode())
            
            # After authentication, send waiting message and proceed with player matching
            client_socket.send("Waiting for another player to join...".encode())
            self.waiting_players.put((client_socket, username))
        except Exception as e:
            print(f"Authentication error: {e}")
            client_socket.close()

    def match_players(self):
        """Match waiting players into game sessions"""
        while self.is_running:
            try:
                # Try to get two players
                if self.waiting_players.qsize() >= 2:
                    player1 = self.waiting_players.get()
                    player2 = self.waiting_players.get()
                    
                    # Notify players that a match is found
                    player1[0].send(f"Match found! You'll be playing against {player2[1]}".encode())
                    player2[0].send(f"Match found! You'll be playing against {player1[1]}".encode())
                    
                    # Create and start game session
                    game_session = GameSession(player1, player2)
                    session_thread = threading.Thread(target=game_session.play_game)
                    session_thread.start()
                    
                    # Keep track of active sessions
                    self.active_sessions.append(session_thread)
            except Exception as e:
                print(f"Error in player matching: {e}")
            
            # Small sleep to prevent tight loop
            time.sleep(1)

    def start(self):
        try:
            # Start player matching thread
            matching_thread = threading.Thread(target=self.match_players)
            matching_thread.start()
            
            print(f"Server started on {self.host}:{self.port}")
            self.server_socket.listen()
            
            while self.is_running:
                try:
                    # Accept incoming connections
                    client_socket, address = self.server_socket.accept()
                    print(f"Connection from {address}")
                    
                    # Handle each connection in a separate thread
                    connection_thread = threading.Thread(
                        target=self.handle_player_connection, 
                        args=(client_socket,)
                    )
                    connection_thread.start()
                
                except Exception as e:
                    if self.is_running:
                        print(f"Error accepting connection: {e}")
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown the server"""
        self.is_running = False
        
        # Close server socket
        try:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
        except:
            pass
        
        # Close all waiting player connections
        while not self.waiting_players.empty():
            try:
                player = self.waiting_players.get_nowait()
                player.close()
            except:
                pass

def main():
    server = RockPaperScissorsServer()
    server.start()

if __name__ == "__main__":
    main()