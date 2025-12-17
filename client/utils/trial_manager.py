import requests
import logging
from client.config.config import TRIAL_CHECK_ELIGIBILITY_URL, TRIAL_CREATE_URL, TRIAL_STATUS_URL
from client.utils.hardware_id import get_cross_platform_hardware_id

logger = logging.getLogger(__name__)

class TrialManager:
    def __init__(self):
        self.hardware_id = get_cross_platform_hardware_id()
        
    def check_trial_status(self):
        """
        Check the current trial status from the server.
        Returns: dict with 'allowed', 'remaining', 'limit', 'count'
        """
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # This is now handled at login time, but kept for compatibility
                response = requests.get(TRIAL_STATUS_URL, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return {'allowed': data.get('is_active', False), 'is_trial': data.get('is_trial', False)}
                else:
                    logger.error(f"Trial check failed: {response.status_code}")
                    return {'allowed': False, 'error': 'server_error'}
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return {'allowed': False, 'error': 'connection_error'}
            except Exception as e:
                logger.error(f"Trial check exception: {e}")
                return {'allowed': False, 'error': 'connection_error'}

    def increment_trial_usage(self, files_count=1):
        """
        No longer needed - trial management is now license-based, not usage-based.
        Trial licenses expire after 1 day, regardless of usage.
        """
        logger.info(f"Trial usage tracking deprecated - trial is 1-day license-based")
        return {'allowed': True, 'count': 0, 'limit': 'unlimited'}

    def reset_trial_usage(self):
        """
        Reset trial - no longer used with license-based system.
        Trial licenses are managed at activation time.
        """
        logger.info("Trial reset not needed - using license-based system")
        return {'success': True}
