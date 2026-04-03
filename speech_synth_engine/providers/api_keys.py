"""
API Key Manager for handling multiple API keys with automatic rotation.
"""
import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class APIKeyManager:
    """
    Manages multiple API keys with automatic rotation when quota is exceeded.
    """
    def __init__(self, provider_name: str, env_var_prefix: str = "ELEVENLABS_API_KEY"):
        """
        Initialize the API key manager.
        
        Args:
            provider_name: Name of the provider (for logging)
            env_var_prefix: Prefix for environment variables containing API keys
        """
        self.provider_name = provider_name
        self.env_var_prefix = env_var_prefix
        self.logger = logging.getLogger(f"APIKeyManager.{provider_name}")
        self._available_keys = self._load_api_keys()
        self._current_key_index = 0
        self._exhausted_keys = set()
        
        if not self._available_keys:
            raise ValueError(f"No API keys found with prefix '{env_var_prefix}'. "
                           f"Please set environment variables like {env_var_prefix}_1, {env_var_prefix}_2, etc.")
        
        self.logger.info(f"Initialized with {len(self._available_keys)} API keys")
    
    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment variables."""
        import re
        keys = []
        indexed_keys = {}
        
        # Load all environment variables
        for var_name, var_value in os.environ.items():
            if var_value and var_value.strip():
                # Check for indexed keys: GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
                match = re.match(f"^{re.escape(self.env_var_prefix)}_(\d+)$", var_name)
                if match:
                    index = int(match.group(1))
                    indexed_keys[index] = var_value.strip()
                # Check for base key: GEMINI_API_KEY
                elif var_name == self.env_var_prefix:
                    keys.append(var_value.strip())
        
        # Add indexed keys in order
        for index in sorted(indexed_keys):
            keys.append(indexed_keys[index])
        
        return keys
    
    def get_current_key(self) -> str:
        """Get the current active API key."""
        if not self._available_keys:
            raise RuntimeError("No API keys available")
        return self._available_keys[self._current_key_index]
    
    def mark_key_exhausted(self, key: str):
        """
        Mark an API key as exhausted (quota exceeded).
        
        Args:
            key: The API key that was exhausted
        """
        if key not in self._available_keys:
            self.logger.warning(f"Attempted to mark unknown key as exhausted")
            return
            
        if key not in self._exhausted_keys:
            self._exhausted_keys.add(key)
            self.logger.warning(f"Marked API key ending with ...{key[-4:]} as exhausted (quota exceeded)")
            
            # If the current key is exhausted, rotate to the next available key
            if key == self.get_current_key():
                self.rotate_key()
    
    def get_next_key(self) -> Optional[str]:
        """
        Get the next available API key without rotating to it.
        
        Returns:
            The next available API key, or None if no more keys are available
        """
        if not self._available_keys:
            return None
            
        next_index = (self._current_key_index + 1) % len(self._available_keys)
        next_key = self._available_keys[next_index]
        
        # Check if we have any non-exhausted keys
        if len(self._exhausted_keys) >= len(self._available_keys):
            self.logger.error("All API keys have been exhausted")
            return None
            
        # If next key is exhausted, try to find the next available one
        if next_key in self._exhausted_keys:
            original_index = next_index
            while next_key in self._exhausted_keys:
                next_index = (next_index + 1) % len(self._available_keys)
                if next_index == original_index:  # Full circle
                    self.logger.error("All API keys have been exhausted")
                    return None
                next_key = self._available_keys[next_index]
                
        return next_key
        
    def rotate_key(self) -> Optional[str]:
        """
        Rotate to the next available API key.
        
        Returns:
            The new active API key, or None if no more keys are available
        """
        next_key = self.get_next_key()
        if next_key:
            self._current_key_index = self._available_keys.index(next_key)
            self.logger.info(f"Rotated to API key ending with ...{next_key[-4:]}")
            return next_key
        return None
    
    def is_quota_exceeded_error(self, error: Exception) -> bool:
        """
        Check if an error indicates that the API quota has been exceeded.
        
        Args:
            error: The exception to check
            
        Returns:
            bool: True if the error indicates a quota exceeded condition
        """
        error_str = str(error).lower()
        return any(term in error_str for term in ["quota", "limit", "exceeded", "429"])
    
    def handle_api_error(self, error: Exception) -> bool:
        """
        Handle an API error and rotate keys if necessary.
        
        Args:
            error: The exception that occurred
            
        Returns:
            bool: True if the error was handled and a retry might succeed
        """
        if self.is_quota_exceeded_error(error):
            current_key = self.get_current_key()
            self.mark_key_exhausted(current_key)
            return True  # Indicate that a retry might succeed
        return False
