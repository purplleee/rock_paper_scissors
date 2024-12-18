import socket
import threading
import time
import math
import random
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
        auth_manager = AuthenticationManager()
    
        if self.scores[self.usernames[0]] > self.scores[self.usernames[1]]:
            self.players[0].send(f"Game Over! You won the series {self.scores[self.usernames[0]]}-{self.scores[self.usernames[1]]}".encode())
            self.players[1].send(f"Game Over! You lost the series {self.scores[self.usernames[0]]}-{self.scores[self.usernames[1]]}".encode())
        
            # Update user stats
            auth_manager.update_user_stats(self.usernames[0], True)
            auth_manager.update_user_stats(self.usernames[1], False)
    
        elif self.scores[self.usernames[1]] > self.scores[self.usernames[0]]:
            self.players[0].send(f"Game Over! You lost the series {self.scores[self.usernames[1]]}-{self.scores[self.usernames[0]]}".encode())
            self.players[1].send(f"Game Over! You won the series {self.scores[self.usernames[1]]}-{self.scores[self.usernames[0]]}".encode())
        
            # Update user stats
            auth_manager.update_user_stats(self.usernames[0], False)
            auth_manager.update_user_stats(self.usernames[1], True)
    
        else:
            for player in self.players:
                player.send("Game Over! The series is a tie!".encode())
                
class Tournament:
    def __init__(self, max_players=16):
        self.players_queue = queue.Queue(maxsize=max_players)
        self.active_players = []
        self.eliminated_players = []
        self.max_rounds = int(math.log2(max_players))  # Dynamically calculate max rounds
        self.current_round = 0
        self.tournament_active = False
        self.tournament_winner = None
        self.lock = threading.Lock()
        
        # New tracking mechanisms
        self.tournament_brackets = []
        self.tournament_status = {
            'total_players': 0,
            'players_remaining': 0,
            'current_round': 0,
            'matches_in_progress': 0
        }

    def add_player(self, player_info):
        """Enhanced player addition with more robust checks"""
        with self.lock:
            # Check if player is already in tournament
            if any(player_info[1] == p[1] for p in self.active_players):
                player_info[0].send("You are already registered in the tournament.".encode())
                return False

            # Validate socket
            try:
                player_info[0].fileno()
            except Exception:
                print(f"Invalid socket for player {player_info[1]}")
                return False

            # Add to active players and update status
            try:
                self.active_players.append(player_info)
                self.tournament_status['total_players'] += 1
                self.tournament_status['players_remaining'] += 1
                
                # Automatically start tournament if max players reached
                if len(self.active_players) == self.players_queue.maxsize:
                    self._start_tournament()
                
                # Notify player
                player_info[0].send(f"Registered for tournament. Current players: {len(self.active_players)}/{self.players_queue.maxsize}".encode())
                return True
            
            except Exception as e:
                print(f"Error adding player to tournament: {e}")
                return False

    def _start_tournament(self):
        """Officially start the tournament and create initial brackets"""
        with self.lock:
            if self.tournament_active:
                return

            self.tournament_active = True
            self.current_round = 1
            self.tournament_status['current_round'] = 1
            
            # Shuffle players to randomize initial matchups
            random.shuffle(self.active_players)
            
            # Create initial tournament brackets
            self.tournament_brackets = [
                self.active_players[i:i+2] 
                for i in range(0, len(self.active_players), 2)
            ]
            
            # Broadcast tournament start
            self._broadcast_tournament_start()

    def _broadcast_tournament_start(self):
        """Send tournament start information to all players"""
        start_message = (
            f"Tournament Started!\n"
            f"Total Players: {len(self.active_players)}\n"
            f"Total Rounds: {self.max_rounds}\n"
            f"First Round Matchups:\n"
        )
        
        # Generate matchup descriptions
        for i, bracket in enumerate(self.tournament_brackets, 1):
            start_message += f"Match {i}: {bracket[0][1]} vs {bracket[1][1]}\n"
        
        # Send to all players
        for player_info in self.active_players:
            try:
                player_info[0].send(start_message.encode())
            except Exception as e:
                print(f"Could not send start message to {player_info[1]}: {e}")

    def update_tournament_progress(self, winner, loser):
        """Update tournament progress after each match"""
        with self.lock:
            # Remove loser from active players
            self.active_players = [p for p in self.active_players if p[1] != loser[1]]
            self.eliminated_players.append(loser)
            
            # Update tournament status
            self.tournament_status['players_remaining'] -= 1
            
            # Check if tournament should progress to next round
            if len(self.active_players) % 2 == 0:
                self._prepare_next_round()
            
            # Check for tournament completion
            if len(self.active_players) == 1:
                self._conclude_tournament(self.active_players[0])

    def _prepare_next_round(self):
        """Prepare next round of tournament"""
        self.current_round += 1
        self.tournament_status['current_round'] = self.current_round
        
        # Recreate brackets with remaining active players
        self.tournament_brackets = [
            self.active_players[i:i+2] 
            for i in range(0, len(self.active_players), 2)
        ]
        
        # Broadcast round progression
        round_message = (
            f"Tournament Progressing to Round {self.current_round}!\n"
            f"Players Remaining: {len(self.active_players)}\n"
            "Next Matchups:\n"
        )
        
        for i, bracket in enumerate(self.tournament_brackets, 1):
            round_message += f"Match {i}: {bracket[0][1]} vs {bracket[1][1]}\n"
        
        # Send to all remaining players
        for player_info in self.active_players:
            try:
                player_info[0].send(round_message.encode())
            except Exception as e:
                print(f"Could not send round update to {player_info[1]}: {e}")

    def _conclude_tournament(self, champion):
        """Finalize tournament and declare winner"""
        with self.lock:
            self.tournament_winner = champion
            self.tournament_active = False
            
            # Broadcast champion
            champion_message = (
                "🏆 TOURNAMENT COMPLETE 🏆\n"
                f"Champion: {champion[1]}!\n"
                f"Total Rounds Played: {self.current_round}"
            )
            
            try:
                champion[0].send(champion_message.encode())
            except Exception as e:
                print(f"Could not send champion message: {e}")
            
            # Optional: Log tournament results
            self._log_tournament_results()

    def _log_tournament_results(self):
        """Log tournament results (can be expanded)"""
        print(f"Tournament Winner: {self.tournament_winner[1]}")
        print(f"Eliminated Players: {[p[1] for p in self.eliminated_players]}")

class RockPaperScissorsServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        
        # Create tournament instance
        self.tournament = Tournament()
        
        # Queue for waiting players
        self.waiting_players = queue.Queue()
        
        # Active game sessions
        self.active_sessions = []
        
        # Flag to control server
        self.is_running = True

    def handle_player_connection(self, client_socket):
        """ Handle player authentication and game mode selection """
        # Ensure client_socket is valid before using it
        if not client_socket:
            print("Invalid client socket received")
            return

        # Create authentication manager
        auth_manager = AuthenticationManager()
        
        try:
            # Send login/register prompt
            client_socket.send("Please login or register (LOGIN/REGISTER username password)".encode())
            
            authenticated = False
            username = None
            
            # Authentication process
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
            
            # Game Mode Selection
            client_socket.send("Choose your game mode: NORMAL or TOURNAMENT".encode())
            mode_response = client_socket.recv(1024).decode().strip().upper()
            
            # Validate game mode
            if mode_response not in ['NORMAL', 'TOURNAMENT']:
                client_socket.send("Invalid game mode. Defaulting to NORMAL.".encode())
                mode_response = 'NORMAL'
            
            # Add player to appropriate queue based on game mode
            if mode_response == 'NORMAL':
                self.waiting_players.put((client_socket, username))
                client_socket.send("You have been added to the normal game queue. Waiting for a match...\n".encode())
            else:  # Tournament mode
                self.tournament.add_player((client_socket, username))
                client_socket.send("You have been added to the tournament queue. Waiting for a match...\n".encode())
        
        except Exception as e:
            print(f"Connection handling error: {e}")
            try:
                client_socket.close()
            except:
                pass

    def match_players(self):
        """Match waiting players into normal game sessions"""
        while self.is_running:
            try:
                # Ensure enough players for a normal game
                if self.waiting_players.qsize() >= 2:
                    # Get two players from the queue
                    player1 = self.waiting_players.get()
                    player2 = self.waiting_players.get()
                    
                    # Notify players that a match is found
                    player1[0].send(f"Match found! You'll be playing against {player2[1]}".encode())
                    player2[0].send(f"Match found! You'll be playing against {player1[1]}".encode())
                    
                    # Create and start a normal game session
                    game_session = GameSession(player1, player2)
                    session_thread = threading.Thread(target=game_session.play_game)
                    session_thread.start()
                    
                    # Keep track of active sessions
                    self.active_sessions.append(session_thread)
                
                # Small sleep to prevent tight loop and reduce CPU usage
                time.sleep(1)
            
            except Exception as e:
                print(f"Error in player matching: {e}")

    def start(self):
    
        try:
            # No need to explicitly start tournament thread here
            # Tournament will start when first player joins
            
            # Start normal game matching thread
            match_players_thread = threading.Thread(target=self.match_players)
            match_players_thread.start()
        
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
