# Client Code
import socket

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
            
            # Get and send player's move
            while True:
                move = input("").strip()
                self.client_socket.send(move.encode())
                
                # Check for any server messages (like invalid move)
                result = self.client_socket.recv(1024).decode()
                if result != "":
                    print(result)
                    break
            
            # Receive final game result
            final_result = self.client_socket.recv(1024).decode()
            print(final_result)
            
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.client_socket.close()

def main():
    client = RockPaperScissorsClient()
    client.connect()

if __name__ == "__main__":
    main()