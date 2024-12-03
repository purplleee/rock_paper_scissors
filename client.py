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
            
            # Receive and display game instructions
            instructions = self.client_socket.recv(1024).decode()
            print(instructions)
            
            # Play through the game series
            while True:
                # Get and send player's move
                move = input("").strip()
                self.client_socket.send(move.encode())
                
                # Check for server messages
                response = self.client_socket.recv(1024).decode()
                print(response)
                
                # Check if game is over
                if "Game Over" in response:
                    break
                
                # Check for additional instructions
                if "Invalid move" in response:
                    continue
                
        except socket.timeout:
            print("Connection timed out.")
        except ConnectionResetError:
            print("Connection was closed by the server.")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.client_socket.close()

def main():
    client = RockPaperScissorsClient()
    client.connect()

if __name__ == "__main__":
    main()