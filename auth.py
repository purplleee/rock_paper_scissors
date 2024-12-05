import hashlib
import os
import json
from typing import Dict, Optional

class AuthenticationManager:
    def __init__(self, database_path='users.json'):
        """
        Initialize authentication manager with a JSON file database
        
        Args:
            database_path (str): Path to the user database file
        """
        self.database_path = database_path
        
        # Create database file if it doesn't exist
        if not os.path.exists(self.database_path):
            with open(self.database_path, 'w') as f:
                json.dump({}, f)
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using SHA-256
        
        Args:
            password (str): Plain text password
        
        Returns:
            str: Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str) -> bool:
        """
        Register a new user
        
        Args:
            username (str): Chosen username
            password (str): User's password
        
        Returns:
            bool: True if registration successful, False if username exists
        """
        # Load existing users
        with open(self.database_path, 'r') as f:
            users = json.load(f)
        
        # Check if username already exists
        if username in users:
            return False
        
        # Create user entry with hashed password and initial stats
        users[username] = {
            'password': self._hash_password(password),
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'rank': 1000  # Starting rank
        }
        
        # Save updated users
        with open(self.database_path, 'w') as f:
            json.dump(users, f, indent=4)
        
        return True
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user
        
        Args:
            username (str): Username
            password (str): Password
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Load existing users
        with open(self.database_path, 'r') as f:
            users = json.load(f)
        
        # Check if user exists and password matches
        if username not in users:
            return False
        
        stored_password = users[username]['password']
        return stored_password == self._hash_password(password)
    
    def update_user_stats(self, username: str, won: bool) -> None:
        """
        Update user game statistics
        
        Args:
            username (str): Username
            won (bool): Whether the user won the game
        """
        # Load existing users
        with open(self.database_path, 'r') as f:
            users = json.load(f)
        
        if username not in users:
            return
        
        # Update statistics
        users[username]['total_games'] += 1
        if won:
            users[username]['wins'] += 1
            # Simple ranking increase
            users[username]['rank'] += 20
        else:
            users[username]['losses'] += 1
            # Prevent rank from going below 1000
            users[username]['rank'] = max(1000, users[username]['rank'] - 10)
        
        # Save updated users
        with open(self.database_path, 'w') as f:
            json.dump(users, f, indent=4)
    
    def get_user_stats(self, username: str) -> Optional[Dict]:
        """
        Retrieve user statistics
        
        Args:
            username (str): Username
        
        Returns:
            Optional[Dict]: User statistics or None if user not found
        """
        with open(self.database_path, 'r') as f:
            users = json.load(f)
        
        return users.get(username)