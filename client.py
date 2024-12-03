import socket
import time

class RockPaperScissorsClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            
            while True:
                # Receive and display server messages
                response = self.client_socket.recv(1024).decode()
                print(response)
                
                # Check for specific prompts
                if "Do you want to play again?" in response:
                    # Prompt for play again
                    play_again = input("").strip().lower()
                    self.client_socket.send(play_again.encode())
                    
                    # Exit if not playing again
                    if play_again != 'yes':
                        print("Thanks for playing!")
                        return
                
                # Check for move prompt
                elif "Enter your choice" in response:
                    # Get and send player's move
                    move = input("").strip()
                    self.client_socket.send(move.encode())
                
                # Check for game over message
                elif "Game Over" in response:
                    # Option to exit or continue
                    print("Game session ended.")
        
        except ConnectionRefusedError:
            print("Unable to connect to the server.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.client_socket.close()

def main():
    client = RockPaperScissorsClient()
    client.connect()

if __name__ == "__main__":
    main()