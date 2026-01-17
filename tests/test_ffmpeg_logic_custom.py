
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Adjust path to find client module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.core.conversion_engine_validation import validate_and_apply_ffmpeg, apply_ffmpeg_to_environment

class TestFFmpegLogic(unittest.TestCase):

    @patch('client.core.conversion_engine_validation.validate_system_ffmpeg')
    @patch('client.core.conversion_engine_validation.apply_ffmpeg_to_environment')
    def test_validate_and_apply_system_success(self, mock_apply, mock_validate):
        # Setup mock to return success for system ffmpeg
        mock_validate.return_value = (True, "", "C:\\fake\\ffmpeg.exe", "N/A")
        
        # Call function
        success, error, path = validate_and_apply_ffmpeg('system')
        
        # Verify
        self.assertTrue(success)
        self.assertEqual(path, "C:\\fake\\ffmpeg.exe")
        # Ensure apply was called WITH the path
        mock_apply.assert_called_with("C:\\fake\\ffmpeg.exe", mode='system')

    @patch('client.core.conversion_engine_validation.validate_system_ffmpeg')
    def test_validate_and_apply_system_failure(self, mock_validate):
        # Setup mock to return failure
        mock_validate.return_value = (False, "Not found", "", "")
        
        # Call function
        success, error, path = validate_and_apply_ffmpeg('system')
        
        # Verify
        self.assertFalse(success)
        
    def test_apply_env_logic(self):
        # Test applying with a specific path in system mode
        with patch.dict(os.environ, {}, clear=True):
            apply_ffmpeg_to_environment("C:\\temp\\ffmpeg.exe", mode='system')
            # Mock os.path.exists for this test since we can't rely on existing file
            with patch('os.path.exists', return_value=True):
                apply_ffmpeg_to_environment("C:\\temp\\ffmpeg.exe", mode='system')
                self.assertEqual(os.environ.get('FFMPEG_BINARY'), "C:\\temp\\ffmpeg.exe")
                
        # Test applying WITHOUT path in system mode (should clear vars)
        with patch.dict(os.environ, {'FFMPEG_BINARY': 'old'}, clear=True):
            apply_ffmpeg_to_environment('', mode='system')
            self.assertIsNone(os.environ.get('FFMPEG_BINARY'))

if __name__ == '__main__':
    unittest.main()
