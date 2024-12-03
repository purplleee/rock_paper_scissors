import socket
import sys
import threading

class RockPaperScissorsClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_running = True

    def receive_messages(self):
        """
        Continuously receive messages from the server
        """
        try:
            while self.is_running:
                try:
                    # Set a short timeout to check is_running
                    self.client_socket.settimeout(1)
                    response = self.client_socket.recv(1024).decode()
                    
                    # Check for server shutdown
                    if not response:
                        print("\nConnection to server lost.")
                        self.shutdown()
                        break
                    
                    print(response)
                    
                    # Check for game over message and exit
                    if "Game Over" in response or "Server is shutting down" in response:
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
            while self.is_running:
                try:
                    # Check for move prompt
                    move = input("").strip()
                    if not self.is_running:
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
        try:
            self.client_socket.close()
        except:
            pass
        
        print("\nThanks for playing! Client shutting down.")
        sys.exit(0)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
            
            # Create threads for receiving and sending messages
            receive_thread = threading.Thread(target=self.receive_messages)
            send_thread = threading.Thread(target=self.send_messages)
            
            # Start threads
            receive_thread.start()
            send_thread.start()
            
            # Wait for threads to complete
            receive_thread.join()
            send_thread.join()
        
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