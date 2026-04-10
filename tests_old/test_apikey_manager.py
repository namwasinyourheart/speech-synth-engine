import sys
sys.path.append("/home/nampv1/projects/tts/speech-synth-engine")

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from speech_synth_engine.providers.api_keys import APIKeyManager

class TestAPIKeyManager:
    """Test cases for APIKeyManager class."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear any existing environment variables
        for key in list(os.environ.keys()):
            if key.startswith('ELEVENLABS_API_KEY'):
                del os.environ[key]
        
        # Set up test API keys
        # self.test_keys = [
        #     'test_key_1234567890',
        #     'test_key_2345678901',
        #     'test_key_3456789012'
        # ]
        self.test_keys = [
            'sk_cff70be83e8227d651c26308d34188e7b8b39091cacbad9f',
            'sk_182eb629066c345f4e5dda4c529b4436a2adc49781f81e02',
        ]
        
        # Set environment variables for testing
        for i, key in enumerate(self.test_keys, 1):
            os.environ[f'ELEVENLABS_API_KEY_{i}'] = key
    
    def test_initialization(self):
        """Test APIKeyManager initialization."""
        manager = APIKeyManager("TestProvider")
        assert manager.get_current_key() == self.test_keys[0]
    
    def test_key_rotation(self):
        """Test key rotation functionality."""
        manager = APIKeyManager("TestProvider")
        
        # Verify initial key
        assert manager.get_current_key() == self.test_keys[0]
        
        # Rotate to next key
        next_key = manager.rotate_key()
        assert next_key == self.test_keys[1]
        assert manager.get_current_key() == self.test_keys[1]
        
        # Rotate back to first key (wrap around)
        assert manager.rotate_key() == self.test_keys[0]  # Should wrap around
    
    def test_mark_key_exhausted(self):
        """Test marking a key as exhausted."""
        manager = APIKeyManager("TestProvider")
        
        # Mark first key as exhausted
        manager.mark_key_exhausted(manager.get_current_key())
        
        # Should automatically rotate to next key
        assert manager.get_current_key() == self.test_keys[1]
        
        # Mark all keys as exhausted
        for key in self.test_keys:
            manager.mark_key_exhausted(key)
        
        # Should return None when no keys left
        assert manager.rotate_key() is None
    
    def test_is_quota_exceeded_error(self):
        """Test quota exceeded error detection."""
        manager = APIKeyManager("TestProvider")
        
        # Test various error messages that should be detected as quota exceeded
        assert manager.is_quota_exceeded_error(Exception("quota exceeded")) is True
        assert manager.is_quota_exceeded_error(Exception("limit reached")) is True
        assert manager.is_quota_exceeded_error(Exception("429")) is True
        assert manager.is_quota_exceeded_error(Exception("quota")) is True
        
        # Test non-quota related errors
        assert manager.is_quota_exceeded_error(Exception("network error")) is False
        assert manager.is_quota_exceeded_error(Exception("invalid key")) is False
    
    def test_handle_api_error(self):
        """Test error handling with automatic key rotation."""
        manager = APIKeyManager("TestProvider")
        initial_key = manager.get_current_key()
        
        # Test with quota exceeded error
        error = Exception("quota exceeded")
        assert manager.handle_api_error(error) is True  # Should indicate retry
        assert manager.get_current_key() != initial_key  # Should have rotated key
        
        # Test with non-quota error
        error = Exception("invalid request")
        assert manager.handle_api_error(error) is False  # Should not retry
    
    def test_load_api_keys_from_config(self):
        """Test loading API keys from config."""
        # Set up test keys with custom prefix first
        custom_keys = ['custom_key_1', 'custom_key_2']
        for i, key in enumerate(custom_keys, 1):
            os.environ[f'CUSTOM_PREFIX_{i}'] = key
        
        # Now initialize the manager
        manager = APIKeyManager("TestProvider", env_var_prefix="CUSTOM_PREFIX")
        
        # Verify the keys are loaded correctly
        assert manager.get_current_key() == custom_keys[0]
        assert manager.rotate_key() == custom_keys[1]
    
    def test_no_keys_available(self):
        """Test behavior when no API keys are available."""
        # Clear all API keys
        for key in list(os.environ.keys()):
            if key.startswith('ELEVENLABS_API_KEY'):
                del os.environ[key]
        
        # Should raise ValueError on initialization
        with pytest.raises(ValueError):
            APIKeyManager("TestProvider")

if __name__ == "__main__":
    pytest.main(["-v", "/home/nampv1/projects/tts/speech-synth-engine/tests/test_apikey_manager.py"])
