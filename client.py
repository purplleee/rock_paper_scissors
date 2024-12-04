import socket
import sys
import threading
import time
from auth import AuthenticationManager 

class RockPaperScissorsClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = True
        self.game_over = False

    def receive_messages(self):
        """
        Continuously receive messages from the server
        """
        try:
            while not self.game_over and self.is_running:
                try:
                    # Set a short timeout to check is_running
                    self.client_socket.settimeout(1)
                    response = self.client_socket.recv(1024).decode()
                    
                    # Check for server shutdown or empty message
                    if not response:
                        print("\nConnection to server lost.")
                        self.shutdown()
                        break
                    
                    print(response)
                    
                    # Check for game over message
                    if "Game Over" in response or "Server is shutting down" in response:
                        self.game_over = True
                        self.shutdown()
                        break
                
                except socket.timeout:
                    # This allows checking is_running periodically
                    continue
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    self.shutdown()
                    break
        except:
            pass

    def send_messages(self):
        """
        Handle sending messages to the server
        """
        try:
            while not self.game_over and self.is_running:
                try:
                    # Check for move prompt
                    move = input("").strip()
                    if not self.is_running or self.game_over:
                        break
                    self.client_socket.send(move.encode())
                except Exception as e:
                    print(f"Error sending message: {e}")
                    self.shutdown()
                    break
        except:
            pass

    def shutdown(self):
        """
        Gracefully shutdown the client
        """
        if not self.is_running:
            return
        
        self.is_running = False
        self.game_over = True
        
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
        except:
            pass
        
        print("\nThanks for playing! Client shutting down.")
        # Use os._exit to immediately terminate all threads
        import os
        os._exit(0)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            
            # Handle authentication
            while True:
                response = self.client_socket.recv(1024).decode()
                print(response)
                
                if "successful" in response.lower():
                    break
                
                # Validation loop for authentication menu
                while True:
                    print("\nAuthentication Menu:")
                    print("1. Login")
                    print("2. Register")
                    action_choice = input("Enter your choice (1/2): ").strip()
                    
                    # Validate menu choice
                    if action_choice in ['1', '2']:
                        # Map numeric choice to action
                        action = "LOGIN" if action_choice == '1' else "REGISTER"
                        break
                    else:
                        print("Invalid choice. Please enter 1 or 2.")
                
                # Prompt for credentials
                username = input("Username: ")
                password = input("Password: ")
                
                # Send authentication request
                message = f"{action} {username} {password}"
                self.client_socket.send(message.encode())
            
            # Create threads for receiving and sending messages
            receive_thread = threading.Thread(target=self.receive_messages)
            send_thread = threading.Thread(target=self.send_messages)
            
            # Set threads as daemon so they'll terminate when main thread ends
            receive_thread.daemon = True
            send_thread.daemon = True
            
            # Start threads
            receive_thread.start()
            send_thread.start()
            
            # Wait for threads to complete or game to end
            while not self.game_over and self.is_running:
                time.sleep(0.1)
            
            # Ensure shutdown
            self.shutdown()
        
        except ConnectionRefusedError:
            print("Unable to connect to the server.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.shutdown()

def main():
    client = RockPaperScissorsClient()
    client.connect()

if __name__ == "__main__":
    main()