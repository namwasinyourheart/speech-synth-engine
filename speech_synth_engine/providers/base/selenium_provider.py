#!/usr/bin/env python3
# ============================================================
# Selenium Provider Base Class
# Base class for all Selenium-based TTS providers
# ============================================================

import os
import time
import logging
import tempfile
import shutil
import subprocess
from abc import abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

try:
    import undetected_chromedriver as uc
except ImportError:
    # Fallback to regular Chrome driver if undetected_chromedriver not available
    uc = None

from .provider import TTSProvider


class SeleniumProvider(TTSProvider):
    """
    Base class for all Selenium-based TTS providers.
    Provides common Selenium functionality and abstract methods for provider-specific implementations.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)

        # Selenium configuration
        self.base_url = self.config.get('base_url', '')
        self.headless = self.config.get('headless', False)
        self.driver_path = self.config.get('driver_path')
        self.window_size = self.config.get('window_size', '1920x1080')
        self.timeout = self.config.get('timeout', 30)
        self.download_timeout = self.config.get('download_timeout', 120)

        # Chrome profile configuration (persistent login)
        # If chrome_profile_name is provided, we will use a persistent profile directory:
        #   chrome_profiles_base_dir / chrome_profile_name
        # Example: /home/nampv1/selenium-chrome-profiles/acc1
        self.chrome_profile_name: Optional[str] = (
            self.config.get('chrome_profile_name')
            or self.config.get('chrome_profile')
            or os.environ.get('CHROME_PROFILE_NAME')
        )
        self.chrome_profiles_base_dir: str = self.config.get(
            'chrome_profiles_base_dir', os.environ.get('CHROME_PROFILES_BASE_DIR', '/home/nampv1/selenium-chrome-profiles')
        )
        # For backward compatibility: allow forcing persistent profile via flag or env
        env_use_persistent = os.environ.get('USE_PERSISTENT_PROFILE')
        self.use_persistent_profile: bool = bool(
            self.config.get('use_persistent_profile', bool(self.chrome_profile_name))
            or (env_use_persistent and env_use_persistent not in ('0', 'false', 'False'))
        )

        # Authentication configuration
        self.auth_config = self.config.get('auth', {})

        # If running in LOGIN_ONLY mode, force a visible browser to allow manual interaction/CAPTCHA
        try:
            if os.environ.get('LOGIN_ONLY') and os.environ.get('LOGIN_ONLY') not in ('0', 'false', 'False'):
                self.headless = False
        except Exception:
            pass

        # Driver instance
        self.driver: Optional[webdriver.Chrome] = None

        # Session management
        self.is_authenticated = False
        self.main_window = None
        self.profile_dir: Optional[str] = None  # Chrome profile directory (temp or persistent)
        self._is_temp_profile: bool = False     # Track if the profile dir is temporary for cleanup

    def setup_driver(self) -> bool:
        """
        Setup Chrome driver with appropriate options.
        Returns True if successful, False otherwise.
        Only undetected_chromedriver is allowed for this provider.
        """
        try:
            if not uc:
                self.logger.error("❌ undetected_chromedriver is required but not installed")
                return False

            # Decide profile directory: persistent (if configured) or temporary
            if self.use_persistent_profile:
                # Build persistent profile path
                if not self.chrome_profile_name:
                    # Allow deriving from shard env variables for convenience
                    # e.g., SHARD_GOOGLE_EMAIL=abc@gmail.com -> profile name 'abc'
                    shard_email = os.environ.get('SHARD_GOOGLE_EMAIL', '')
                    if shard_email:
                        self.chrome_profile_name = shard_email.split('@')[0]
                base_dir = self.chrome_profiles_base_dir
                os.makedirs(base_dir, exist_ok=True)
                if not self.chrome_profile_name:
                    # Fall back to a generic name if none provided
                    self.chrome_profile_name = f"profile_{os.getpid()}"
                self.profile_dir = os.path.join(base_dir, self.chrome_profile_name)
                os.makedirs(self.profile_dir, exist_ok=True)
                self._is_temp_profile = False
            else:
                # Create an isolated temporary Chrome profile dir for this instance
                # This avoids profile locking/conflicts when running multiple scripts concurrently
                self.profile_dir = tempfile.mkdtemp(prefix="uc_profile_")
                self._is_temp_profile = True

            options = Options()

            # Basic options
            if self.headless:
                # Use new headless for Chrome 109+
                options.add_argument('--headless=new')

            # Stability and isolation
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument(f'--window-size={self.window_size}')
            # Use the chosen profile directory (persistent or temporary)
            options.add_argument(f'--user-data-dir={self.profile_dir}')
            options.add_argument('--profile-directory=Default')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument("--remote-debugging-port=" + str(9222 + os.getpid() % 1000))

            # Reduce automation fingerprinting
            # options.add_experimental_option('excludeSwitches', ['enable-automation'])
            # options.add_experimental_option('useAutomationExtension', False)

            # Detect Chrome major version
            try:
                chrome_version = int(subprocess.check_output([
                    "google-chrome", "--version"
                ]).decode().split()[2].split(".")[0])
            except Exception as e:
                self.logger.warning(f"⚠️ Could not detect Chrome version: {e}. Proceeding without version_main")
                chrome_version = None

            # Launch undetected_chromedriver
            try:
                uc_kwargs = {
                    'options': options,
                    'use_subprocess': True,
                }
                if chrome_version is not None:
                    uc_kwargs['version_main'] = chrome_version

                if self.driver_path:
                    from selenium.webdriver.chrome.service import Service
                    service = Service(executable_path=self.driver_path)
                    self.driver = uc.Chrome(service=service, **uc_kwargs)
                else:
                    self.driver = uc.Chrome(**uc_kwargs)

                # Extra hardening to hide webdriver flag (uc normally handles this)
                try:
                    self.driver.execute_script(
                        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                    )
                except Exception:
                    pass

                profile_mode = "persistent" if not self._is_temp_profile else "temporary"
                self.logger.info(f"✅ Using undetected_chromedriver with {profile_mode} profile")
                try:
                    self.logger.info(f"   📁 Chrome profile dir: {self.profile_dir}")
                except Exception:
                    pass
                return True
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize undetected_chromedriver: {e}")
                # Cleanup temp profile dir on failure
                try:
                    if self._is_temp_profile and self.profile_dir and os.path.isdir(self.profile_dir):
                        shutil.rmtree(self.profile_dir, ignore_errors=True)
                        self.profile_dir = None
                except Exception:
                    pass
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to setup driver: {e}")
            # Cleanup temp profile dir on failure
            try:
                if self._is_temp_profile and self.profile_dir and os.path.isdir(self.profile_dir):
                    shutil.rmtree(self.profile_dir, ignore_errors=True)
                    self.profile_dir = None
            except Exception:
                pass
            return False



    
    def navigate_to_base_url(self) -> bool:
        """Navigate to the provider's base URL"""
        if not self.driver:
            self.logger.error("❌ Driver not initialized")
            return False

        try:
            self.logger.info(f"🌐 Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to navigate to base URL: {e}")
            return False

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the provider.
        Each provider must implement their specific authentication flow.
        """
        pass

    @abstractmethod
    def generate_voice(self, text: str, reference_audio: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
        """
        Generate voice from text, optionally with reference audio for cloning.
        Returns (success, audio_url) tuple.
        """
        pass

    def download_audio(self, audio_url: str, output_file: Path) -> bool:
        """
        Download audio from URL to output file.
        Common implementation that can be overridden by specific providers.
        """
        try:
            import requests

            self.logger.info(f"📥 Downloading audio from: {audio_url}")
            response = requests.get(audio_url, timeout=self.download_timeout)

            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)

                if output_file.exists() and output_file.stat().st_size > 0:
                    self.logger.info(f"✅ Audio downloaded successfully: {output_file}")
                    return True
                else:
                    self.logger.error("❌ Downloaded file is empty or doesn't exist")
                    return False
            else:
                self.logger.error(f"❌ Failed to download audio: HTTP {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error downloading audio: {e}")
            return False

    def wait_for_element(self, by: By, value: str, timeout: int = None) -> Optional[Any]:
        """Wait for element to be present and return it"""
        if timeout is None:
            timeout = self.timeout

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"❌ Timeout waiting for element: {by}={value}")
            return None

    def wait_for_clickable(self, by: By, value: str, timeout: int = None) -> Optional[Any]:
        """Wait for element to be clickable and return it"""
        if timeout is None:
            timeout = self.timeout

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"❌ Timeout waiting for clickable element: {by}={value}")
            return None

    def safe_click(self, element: Any) -> bool:
        """Safely click an element with error handling"""
        try:
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to click element: {e}")
            return False

    def safe_send_keys(self, element: Any, keys: str) -> bool:
        """Safely send keys to an element with error handling"""
        try:
            element.clear()
            element.send_keys(keys)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to send keys: {e}")
            return False

    def scroll_to_element(self, element: Any) -> bool:
        """Scroll element into view"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Brief pause after scrolling
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to scroll to element: {e}")
            return False

    def switch_to_new_window(self, main_window: str) -> bool:
        """Switch to new window/tab"""
        try:
            WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)
            new_window = [w for w in self.driver.window_handles if w != main_window][0]
            self.driver.switch_to.window(new_window)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to switch to new window: {e}")
            return False

    def close_extra_windows(self, main_window: str) -> None:
        """Close all windows except the main one"""
        try:
            for handle in self.driver.window_handles:
                if handle != main_window:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
            self.driver.switch_to.window(main_window)
        except Exception as e:
            self.logger.error(f"❌ Error closing extra windows: {e}")

    def take_screenshot(self, filename: str = "selenium_error.png") -> str:
        """Take screenshot for debugging"""
        try:
            screenshot_path = Path(filename)
            self.driver.save_screenshot(str(screenshot_path))
            self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            self.logger.error(f"❌ Failed to take screenshot: {e}")
            return ""

    def cleanup(self) -> None:
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🧹 Driver cleaned up successfully")
            except Exception as e:
                self.logger.error(f"❌ Error during driver cleanup: {e}")
            finally:
                self.driver = None
                self.is_authenticated = False
        # Remove temporary profile directory if created (do not remove persistent profiles)
        try:
            if self._is_temp_profile and self.profile_dir and os.path.isdir(self.profile_dir):
                shutil.rmtree(self.profile_dir, ignore_errors=True)
                self.profile_dir = None
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to remove temp profile dir: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

    def synthesize(self, text: str, voice: str, output_file: Path) -> bool:
        """
        Main synthesize method implementing the TTSProvider interface.
        """
        try:
            # Setup driver if not already done
            if not self.driver:
                if not self.setup_driver():
                    return False

            # Navigate to base URL
            if not self.navigate_to_base_url():
                return False

            # Authenticate if not already authenticated
            if not self.is_authenticated:
                if not self.authenticate():
                    self.logger.error("❌ Authentication failed")
                    return False

            # Generate voice
            success, audio_url = self.generate_voice(text)

            if not success or not audio_url:
                self.logger.error("❌ Voice generation failed")
                return False

            # Download audio
            return self.download_audio(audio_url, output_file)

        except Exception as e:
            self.logger.error(f"❌ Synthesis error: {e}")
            self.take_screenshot()
            return False

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Clone voice using reference audio.
        """
        try:
            # Setup driver if not already done
            if not self.driver:
                if not self.setup_driver():
                    return False

            # Navigate to base URL
            if not self.navigate_to_base_url():
                return False

            # Authenticate if not already authenticated
            if not self.is_authenticated:
                if not self.authenticate():
                    self.logger.error("❌ Authentication failed")
                    return False

            # Generate voice with reference audio
            success, audio_url = self.generate_voice(text, reference_audio)

            if not success or not audio_url:
                self.logger.error("❌ Voice cloning failed")
                return False

            # Download audio
            return self.download_audio(audio_url, output_file)

        except Exception as e:
            self.logger.error(f"❌ Cloning error: {e}")
            self.take_screenshot()
            return False
