#!/usr/bin/env python3
# ============================================================
# MiniMax Selenium Provider
# TTS provider using MiniMax voice cloning via Selenium automation
# ============================================================

import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from .base.selenium_provider import SeleniumProvider


class MiniMaxSeleniumProvider(SeleniumProvider):
    """
    MiniMax TTS provider using Selenium automation for voice cloning.
    Supports both direct synthesis and voice cloning from reference audio.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)

        # MiniMax specific configuration
        self.google_email = self.config.get('google_email', '')
        self.google_password = self.config.get('google_password', '')
        self.base_url = self.config.get('base_url', 'https://www.minimax.io/audio/voices-cloning')

        # Voice generation settings
        self.language = self.config.get('language', 'Vietnamese')
        self.max_wait_time = self.config.get('max_wait_time', 300)  # 5 minutes max

    def _get_supported_voices(self) -> List[str]:
        """MiniMax supports voice cloning, so we return generic voice names"""
        return ["cloned_voice", "reference_voice"]

    def authenticate(self) -> bool:
        """
        Authenticate with MiniMax using Google OAuth.
        Based on the workflow from selenium_vc.py
        """
        try:
            self.logger.info("🔐 Starting MiniMax authentication...")

            # Store main window handle
            self.main_window = self.driver.current_window_handle
            
            # Check and handle CAPTCHA if present
            if not self._handle_captcha():
                self.logger.warning("⚠️ CAPTCHA handling failed or was not completed")

            # 1. Click "Sign In" button
            signin_btn = self.wait_for_clickable(
                By.XPATH,
                "//*[@id='video-user-component']//div[contains(text(),'Sign In')]"
            )

            if not signin_btn or not self.safe_click(signin_btn):
                self.logger.error("❌ Sign In button not found or not clickable")
                return False

            # 2. Click "Continue with Google"
            google_btn = self.wait_for_clickable(
                By.XPATH,
                "//button[.//span[contains(text(), 'Continue with Google')]]"
            )

            if not google_btn or not self.safe_click(google_btn):
                self.logger.error("❌ Continue with Google button not found")
                return False

            # 3. Switch to Google OAuth window
            if not self.switch_to_new_window(self.main_window):
                return False

            # 4. Enter email
            email_input = self.wait_for_clickable(By.ID, "identifierId")
            if not email_input or not self.safe_send_keys(email_input, self.google_email):
                self.logger.error("❌ Email input not found")
                return False

            # Click Next
            next_btn = self.wait_for_clickable(By.ID, "identifierNext")
            if not next_btn or not self.safe_click(next_btn):
                return False

            # 5. Enter password
            password_input = self.wait_for_clickable(By.NAME, "Passwd")
            if not password_input or not self.safe_send_keys(password_input, self.google_password):
                self.logger.error("❌ Password input not found")
                return False

            # Click Sign In
            password_next_btn = self.wait_for_clickable(By.ID, "passwordNext")
            if not password_next_btn or not self.safe_click(password_next_btn):
                return False

            # 6. Wait for authentication to complete and return to main window
            self.logger.info("⏳ Waiting for authentication to complete...")
            # Wait for window count to return to 1 (authentication completed)
            timeout = 60
            start_time = time.time()
            while time.time() - start_time < timeout:
                if len(self.driver.window_handles) == 1:
                    break
                time.sleep(0.5)
            else:
                self.logger.error("❌ Authentication timeout - window count didn't return to 1")
                return False

            self.driver.switch_to.window(self.main_window)

            # 7. Close "Get Started" modal if present
            try:
                get_started_modal = self.wait_for_element(
                    By.XPATH,
                    "//section[contains(@class,'live-modal')]",
                    timeout=5
                )

                if get_started_modal:
                    close_btn = get_started_modal.find_element(By.XPATH, ".//header/button")
                    self.safe_click(close_btn)
                    self.logger.info("✅ Closed Get Started modal")
            except Exception as e:
                self.logger.info("ℹ️ No Get Started modal found (already authenticated)")

            self.is_authenticated = True
            self.logger.info("✅ MiniMax authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            self.take_screenshot("minimax_auth_error.png")
            self.close_extra_windows(self.main_window)
            return False

    def _wait_for_captcha_to_resolve(self, timeout: int = 120) -> bool:
        """
        Wait for CAPTCHA to resolve itself automatically.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if CAPTCHA was resolved or not present, False if timeout
        """
        self.logger.info("⏳ Waiting for CAPTCHA to resolve automatically...")
        start_time = time.time()
        
        def is_captcha_visible():
            try:
                # Check common CAPTCHA elements
                captcha_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "#TktRY1, div[role='alert'], .cb-c, iframe[title*='challenge'], " \
                    "iframe[src*='turnstile'], iframe[src*='cloudflare']"
                )
                return any(element.is_displayed() for element in captcha_elements)
            except:
                return False
        
        # Initial check
        if not is_captcha_visible():
            self.logger.info("✅ No CAPTCHA found, continuing...")
            return True
            
        # Wait for CAPTCHA to disappear
        while time.time() - start_time < timeout:
            if not is_captcha_visible():
                self.logger.info("✅ CAPTCHA resolved automatically")
                return True
                
            # Take periodic screenshots for debugging
            if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                self.take_screenshot(f"captcha_wait_{int(time.time())}.png")
                self.logger.info(f"⏳ Still waiting for CAPTCHA to resolve... "
                              f"({int(time.time() - start_time)}s elapsed)")
            
            time.sleep(1)
        
        self.logger.warning(f"⚠️ CAPTCHA did not resolve within {timeout} seconds")
        self.take_screenshot("captcha_timeout.png")
        return False

    def _handle_captcha(self, max_attempts: int = 5) -> bool:
        """
        Handle CAPTCHA by waiting for it to resolve automatically.
        
        Args:
            max_attempts: Not used, kept for backward compatibility
            
        Returns:
            bool: Always returns True to continue execution
        """
        try:
            # Wait for CAPTCHA to resolve with a 2-minute timeout
            self._wait_for_captcha_to_resolve(timeout=120)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in CAPTCHA handling: {e}")
            self.take_screenshot("captcha_error.png")
            return True  # Continue anyway to avoid blocking the flow

    def _upload_reference_audio(self, reference_audio: Path) -> bool:
        """
        Upload reference audio file for voice cloning.
        """
        try:
            self.logger.info(f"📤 Uploading reference audio: {reference_audio}")

            # Check if file is valid
            if not reference_audio.exists():
                self.logger.error(f"❌ Reference audio file does not exist: {reference_audio}")
                return False

            file_size = reference_audio.stat().st_size
            self.logger.info(f"📊 Reference audio size: {file_size / 1024:.1f} KB")

            if file_size == 0:
                self.logger.error("❌ Reference audio file is empty. Please provide a valid audio file.")
                return False

            # Check if file already uploaded (look for duration display)
            duration_xpath = "//*[@id='voices-cloning-form']//div[contains(@class,'flex-1')]//span[contains(text(), \"''\")]"
            uploaded_elements = self.driver.find_elements(By.XPATH, duration_xpath)

            if uploaded_elements:
                self.logger.info("✅ Reference audio already uploaded")
                return True

            # Upload new file
            upload_input = self.wait_for_element(
                By.XPATH,
                '//*[@id="voices-cloning-form"]//input[@type="file"]'
            )

            if not upload_input:
                self.logger.error("❌ Upload input not found")
                return False

            # Send file path to input
            upload_input.send_keys(str(reference_audio.absolute()))
            self.logger.info("✅ File path sent to upload input")

            # Wait for upload to complete (duration appears)
            self.logger.info("⏳ Waiting for upload to complete...")
            upload_start_time = time.time()

            # Check periodically for upload completion
            while time.time() - upload_start_time < self.max_wait_time:
                uploaded_elements = self.driver.find_elements(By.XPATH, duration_xpath)
                if uploaded_elements:
                    self.logger.info("✅ Reference audio uploaded successfully")
                    return True

                # Check for error messages
                error_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class,'error') or contains(@class,'ant-message-error')]")
                if error_elements:
                    error_text = error_elements[0].text if error_elements else "Unknown error"
                    self.logger.error(f"❌ Upload error detected: {error_text}")
                    return False

                time.sleep(2)  # Check every 2 seconds

            self.logger.error(f"❌ Upload timeout after {self.max_wait_time} seconds")
            self.take_screenshot("minimax_upload_timeout.png")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error uploading reference audio: {e}")
            self.take_screenshot("minimax_upload_error.png")
            return False

    def _select_language(self, language: str = "Vietnamese") -> bool:
        """
        Select language from dropdown using base helper methods.
        Returns True if successful, False otherwise.
        """
        try:
            self.logger.info(f"🌐 Selecting language: {language}")

            # 1. Find and click language dropdown
            language_dropdown = self.wait_for_clickable(
                By.XPATH,
                "//*[@id='voices-cloning-form']//div[contains(@class,'ant-select') and contains(@class,'custom-select')]"
            )
            if not language_dropdown or not self.safe_click(language_dropdown):
                self.logger.error("❌ Failed to open language dropdown")
                return False

            # 2. Wait for dropdown menu to be visible
            language_menu = self.wait_for_element(
                By.XPATH,
                "//div[contains(@class,'ant-select-dropdown') and not(contains(@style,'display: none'))]"
            )
            if not language_menu:
                self.logger.error("❌ Language dropdown menu not found")
                return False
            
            # 3. Find and select Vietnamese option
            max_scrolls = 20
            for _ in range(max_scrolls):
                try:
                    # Try to find Vietnamese option
                    vietnamese_option = language_menu.find_element(
                        By.XPATH,
                        ".//div[contains(text(),'Vietnamese')]"
                    )
                    
                    # Scroll to make it visible using base helper
                    if not self.scroll_to_element(vietnamese_option):
                        self.logger.warning("⚠️ Could not scroll to language option")
                        
                    # First try direct click, if that fails try JavaScript click
                    try:
                        if self.safe_click(vietnamese_option):
                            self.logger.info("✅ Selected Vietnamese language (direct click)")
                    except Exception as e:
                        # If direct click fails, try JavaScript click
                        try:
                            self.driver.execute_script("arguments[0].click();", vietnamese_option)
                            self.logger.info("✅ Selected Vietnamese language (JavaScript click)")
                        except Exception as js_e:
                            self.logger.warning(f"⚠️ Both direct and JS click failed: {js_e}")
                            continue
                    
                    # Wait for dropdown to close and verify selection
                    time.sleep(0.5)  # Small delay for UI update
                    
                    # Verify selection
                    if "Vietnamese" in language_dropdown.text.strip():
                        self.logger.info("✅ Language selection confirmed")
                        return True
                    
                except NoSuchElementException:
                    # If element not found, try scrolling down
                    language_menu.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.3)
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️ Warning in language selection: {e}")
                    continue

            self.logger.error("❌ Failed to select Vietnamese language after multiple attempts")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error selecting language: {e}")
            return False

    def _generate_voice_from_text(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Generate voice from text input.
        Returns (success, audio_url) tuple.
        """
        try:
            self.logger.info(f"🎤 Generating voice for text: {text[:50]}...")

            # 1. Clear and input text
            textarea = self.driver.find_element(By.XPATH, "//*[@id='voices-cloning-form']//textarea")
            if not textarea:
                self.logger.error("❌ Text input textarea not found")
                return False, None

            textarea.click()
            textarea.send_keys(Keys.CONTROL, 'a')
            textarea.send_keys(Keys.BACKSPACE)
            time.sleep(0.2)
            textarea.send_keys(text)

            # 2. Ensure checkbox is ticked
            checkbox = self.driver.find_element(By.XPATH, "//*[@id='voices-cloning-form']//input[@type='checkbox']")
            # if not checkbox.is_selected():
            #     self.safe_click(checkbox)

            
            for attempt in range(1, 3):
                try:
                    if not checkbox.is_selected():
                        self.safe_click(checkbox)
                    break
                except Exception as e:
                    self.logger.info(f"[Attempt {attempt}] Warning in checkbox selection: {e}. Retrying...")
                    time.sleep(0.5)
            else:
                self.logger.warning("⚠️ Failed to select checkbox after multiple attempts")
            
            

            # 3. Click Generate/Regenerate button
            self.logger.info("⏳ Waiting for Generate or Regenerate button to appear...")
            generate_button = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//*[@id='voices-cloning-form']//button[.//span[normalize-space()='Generate'] or .//span[normalize-space()='Regenerate']]"
                ))
            )

            # Cuộn đến nút (scroll vào tầm nhìn)
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", generate_button)
            time.sleep(0.5)  # đợi nhẹ cho hiệu ứng cuộn

            # Retry click logic: click and wait in short windows; if no audio appears, click again
            generate_xpath = (
                "//*[@id='voices-cloning-form']//button"
                "[.//span[normalize-space()='Generate'] or .//span[normalize-space()='Regenerate']]"
            )

            max_retries = int(self.config.get('generate_retries', 3))
            per_attempt_wait = int(self.config.get('generate_retry_wait', 20))  # seconds
            overall_deadline = time.time() + int(self.max_wait_time)

            audio_element = None

            for attempt in range(1, max_retries + 1):
                # Re-find the button each attempt in case DOM changed
                try:
                    generate_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, generate_xpath))
                    )
                except Exception:
                    self.logger.warning("⚠️ Generate button not clickable; trying to locate again by presence")
                    generate_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, generate_xpath))
                    )

                # Scroll into view before clicking
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", generate_button)
                except Exception:
                    pass
                time.sleep(0.3)

                # Click the button (safe click with fallback)
                clicked = self.safe_click(generate_button)
                if not clicked:
                    try:
                        self.driver.execute_script("arguments[0].click();", generate_button)
                        clicked = True
                    except Exception as click_e:
                        self.logger.warning(f"⚠️ JS click failed on attempt {attempt}: {click_e}")

                if clicked:
                    self.logger.info(f"✅ Clicked 'Generate' button (attempt {attempt}/{max_retries}).")
                else:
                    self.logger.warning(f"⚠️ Could not click 'Generate' button (attempt {attempt}/{max_retries}).")

                # Wait for audio to appear within per-attempt window but not exceeding overall max_wait_time
                attempt_deadline = min(overall_deadline, time.time() + per_attempt_wait)
                last_button_state = "Generating"
                
                while time.time() < attempt_deadline:
                    try:
                        # Check for audio element
                        found = self.driver.find_elements(By.XPATH, "//h2[contains(text(), 'Generated Voice Results')]/following::audio[1]")
                        if found:
                            audio_element = found[0]
                            break
                    except Exception:
                        pass

                    # Optional: detect obvious error to break early
                    try:
                        error_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class,'error') or contains(@class,'ant-message-error')]")
                        if error_elements:
                            self.logger.error(f"❌ Error message detected after clicking Generate: {error_elements[0].text}")
                            break
                    except Exception:
                        pass

                    time.sleep(1.5)

                if audio_element:
                    break

                # If overall time exceeded, stop retrying
                if time.time() >= overall_deadline:
                    self.logger.error("❌ Overall generation wait time exceeded while retrying clicks")
                    break

                # Otherwise, prepare to retry
                self.logger.info("↻ No audio yet; retrying click on 'Generate'...")

            # After retries, ensure we have the audio element
            if not audio_element:
                self.logger.error("❌ Generated audio element not found after retries")
                return False, None

            # 5. Extract audio URL
            audio_url = audio_element.get_attribute("src")
            if not audio_url:
                self.logger.error("❌ Audio URL not found in audio element")
                return False, None

            self.logger.info(f"🔗 Audio URL obtained: {audio_url}")
            return True, audio_url

        except Exception as e:
            self.logger.error(f"❌ Error generating voice: {e}")
            self.take_screenshot("minimax_generation_error.png")
            return False, None

    def generate_voice(self, text: str, reference_audio: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
        """
        Generate voice from text, optionally with reference audio for cloning.
        For MiniMax, reference audio is typically required for voice cloning.
        """
        try:
            # For MiniMax voice cloning, reference audio is usually required
            # If no reference audio provided, check if one is already uploaded
            if not reference_audio:
                self.logger.info("ℹ️ No reference audio provided, checking if one is already uploaded...")
                duration_xpath = "//*[@id='voices-cloning-form']//div[contains(@class,'flex-1')]//span[contains(text(), "''")]"
                uploaded_elements = self.driver.find_elements(By.XPATH, duration_xpath)

                if not uploaded_elements:
                    self.logger.error("❌ No reference audio uploaded and none provided. Please provide a reference audio file for voice cloning.")
                    return False, None

                self.logger.info("✅ Using previously uploaded reference audio")
            else:
                # Upload reference audio if provided (for cloning)
                reference_audio = Path(reference_audio)
                if reference_audio.exists():
                    if not self._upload_reference_audio(reference_audio):
                        return False, None
                    self.logger.info(f"✅ Uploaded reference audio: {reference_audio}")

            # Select language (only once per session)
            if not hasattr(self, '_language_selected'):
                if not self._select_language(self.language):
                    return False, None
                self._language_selected = True

            # Generate voice from text using the existing method
            return self._generate_voice_from_text(text)

        except Exception as e:
            self.logger.error(f"❌ Error in generate_voice: {e}")
            self.take_screenshot("minimax_generate_voice_error.png")
            return False, None

    def synthesize_with_metadata(self, text: str, voice: str, output_file: Path) -> Dict[str, Any]:
        """
        Synthesize with comprehensive metadata information.
        For MiniMax, this requires a reference audio for voice cloning.
        """
        result = {
            'success': False,
            'text': text,
            'voice': voice,
            'output_file': str(output_file),
            'provider': self.name,
            'sample_rate': self.sample_rate,
            'language': self.language,
            'estimated_duration': self.estimate_duration(text),
            'error': None,
            'file_info': {},
            'audio_url': None
        }

        try:
            # For MiniMax voice cloning, reference audio is required
            # Check if one is already uploaded or try to find a default one
            reference_audio = self._find_reference_audio()

            if not reference_audio:
                result['error'] = "No reference audio uploaded and none provided. Please provide a reference audio file for voice cloning."
                return result

            # Setup driver and authenticate
            if not self.driver:
                if not self.setup_driver():
                    result['error'] = "Failed to setup driver"
                    return result

            if not self.navigate_to_base_url():
                result['error'] = "Failed to navigate to MiniMax"
                return result

            if not self.is_authenticated:
                if not self.authenticate():
                    result['error'] = "Authentication failed"
                    return result

            # Generate voice with reference audio (MiniMax voice cloning)
            success, audio_url = self.generate_voice(text, reference_audio)

            if not success or not audio_url:
                result['error'] = "Voice generation failed"
                return result

            result['audio_url'] = audio_url

            # Download audio
            if self.download_audio(audio_url, output_file):
                result['success'] = True
                result['file_info'] = self.get_file_info(output_file)
                self.logger.info(f"✅ MiniMax synthesis successful: {output_file}")
            else:
                result['error'] = "Audio download failed"

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ MiniMax synthesis error: {e}")
            self.take_screenshot("minimax_synthesis_error.png")

        finally:
            self.cleanup()

        return result

    def _find_reference_audio(self) -> Optional[Path]:
        """
        Try to find an uploaded reference audio or look for a default one.
        """
        try:
            # Check if reference audio is already uploaded by looking for duration display
            duration_xpath = "//*[@id='voices-cloning-form']//div[contains(@class,'flex-1')]//span[contains(text(), \"''\")]"
            uploaded_elements = self.driver.find_elements(By.XPATH, duration_xpath)

            if uploaded_elements:
                self.logger.info("✅ Found already uploaded reference audio")
                return Path("uploaded")  # Placeholder for already uploaded audio

            # Look for common reference audio files in test directories
            reference_sources = [
                Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/audio/test.wav"),
                Path("/media/nampv1/hdd/data/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10-20251024T103708Z-1-001/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10/spk2_1.m4a")
            ]

            for source in reference_sources:
                if source.exists() and source.stat().st_size > 1000:
                    return source

            return None

        except Exception as e:
            self.logger.warning(f"Error finding reference audio: {e}")
            return None

    def clone_with_metadata(self, text: str, reference_audio: Path, output_file: Path) -> Dict[str, Any]:
        """
        Clone voice with comprehensive metadata information.
        This is the main method for MiniMax voice cloning with detailed results.
        """
        result = {
            'success': False,
            # 'text': text,
            # 'voice': 'cloned_voice',
            # 'output_file': str(output_file),
            # 'provider': self.name,
            # 'sample_rate': self.sample_rate,
            # 'language': self.language,
            # 'estimated_duration': self.estimate_duration(text),
            'error': None,
            # 'file_info': {},
            # 'audio_url': None,
            # 'reference_audio': str(reference_audio)
        }

        try:
            # Setup driver and authenticate (only once)
            if not hasattr(self, '_initialized') or not self._initialized:
                if not self.driver and not self.setup_driver():
                    result['error'] = "Failed to setup driver"
                    return result

                if not self.navigate_to_base_url():
                    result['error'] = "Failed to navigate to MiniMax"
                    return result

                if not self.is_authenticated and not self.authenticate():
                    result['error'] = "Authentication failed"
                    return result
                
                self._initialized = True

            # Generate voice with reference audio
            success, audio_url = self.generate_voice(text, reference_audio)

            if not success or not audio_url:
                result['error'] = "Voice generation failed"
                return result

            # result['audio_url'] = audio_url

            # Download audio
            if self.download_audio(audio_url, output_file):
                result['success'] = True
                # result['file_info'] = self.get_file_info(output_file)
                self.logger.info(f"✅ MiniMax voice cloning successful")
            else:
                result['error'] = "Audio download failed"

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ MiniMax voice cloning error: {e}")
            self.take_screenshot("minimax_cloning_error.png")

        return result

    def clone_batch(self, text_file: Path, reference_audio: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Clone voice and synthesize multiple texts from a file.
        This is the main method for batch MiniMax voice cloning.
        """
        try:
            # Import TextFileLoader
            from ..dataset.text_loaders import TextFileLoader

            self.logger.info(f"🎭 Starting batch voice cloning with reference: {reference_audio}")
            self.logger.info(f"📄 Loading texts from: {text_file}")
            self.logger.info(f"📁 Output directory: {output_dir}")

            # Load texts from file
            loader = TextFileLoader(text_file)
            text_items = loader.load()

            if not text_items:
                self.logger.error("❌ No texts loaded from file")
                return {'success': False, 'error': 'No texts loaded', 'processed': 0, 'failed': 0}

            self.logger.info(f"✅ Loaded {len(text_items)} texts for processing")

            # Setup driver and authenticate once
            if not self.driver:
                if not self.setup_driver():
                    return {'success': False, 'error': 'Failed to setup driver', 'processed': 0, 'failed': len(text_items)}

            if not self.navigate_to_base_url():
                return {'success': False, 'error': 'Failed to navigate to MiniMax', 'processed': 0, 'failed': len(text_items)}

            if not self.is_authenticated:
                if not self.authenticate():
                    self.logger.error("❌ Authentication failed")
                    return {'success': False, 'error': 'Authentication failed', 'processed': 0, 'failed': len(text_items)}

            # Process each text
            results = []
            processed = 0
            failed = 0

            for text_id, text in text_items:
                try:
                    self.logger.info(f"🎤 Processing text {processed + 1}/{len(text_items)}: {text_id}")

                    # Generate output filename
                    safe_id = "".join(c for c in text_id if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    output_file = output_dir / f"minimax_{safe_id}.wav"

                    # Generate voice with reference audio
                    success, audio_url = self.generate_voice(text, reference_audio)

                    if success and audio_url:
                        # Download audio
                        if self.download_audio(audio_url, output_file):
                            results.append({
                                'id': text_id,
                                'text': text,
                                'output_file': str(output_file),
                                'success': True,
                                'audio_url': audio_url
                            })
                            processed += 1
                            self.logger.info(f"✅ Generated: {output_file}")
                        else:
                            results.append({
                                'id': text_id,
                                'text': text,
                                'output_file': str(output_file),
                                'success': False,
                                'error': 'Download failed'
                            })
                            failed += 1
                            self.logger.error(f"❌ Download failed: {output_file}")
                    else:
                        results.append({
                            'id': text_id,
                            'text': text,
                            'output_file': str(output_file),
                            'success': False,
                            'error': 'Generation failed'
                        })
                        failed += 1
                        self.logger.error(f"❌ Generation failed: {text_id}")

                    # Brief pause between requests to avoid overwhelming the service
                    import time
                    time.sleep(2)

                except Exception as e:
                    results.append({
                        'id': text_id,
                        'text': text,
                        'output_file': str(output_dir / f"minimax_{text_id}.wav"),
                        'success': False,
                        'error': str(e)
                    })
                    failed += 1
                    self.logger.error(f"❌ Error processing {text_id}: {e}")

            # Summary
            success_rate = processed / len(text_items) * 100 if text_items else 0

            batch_result = {
                'success': failed == 0,
                'total_texts': len(text_items),
                'processed': processed,
                'failed': failed,
                'success_rate': success_rate,
                'results': results,
                'reference_audio': str(reference_audio),
                'output_directory': str(output_dir)
            }

            self.logger.info(f"📊 Batch processing complete: {processed}/{len(text_items)} successful ({success_rate:.1f}%)")

            return batch_result

        except Exception as e:
            self.logger.error(f"❌ Batch cloning error: {e}")
            self.take_screenshot("minimax_batch_error.png")
            return {'success': False, 'error': str(e), 'processed': 0, 'failed': 0}

        finally:
            self.cleanup()

    def synthesize_batch(self, text_file: Path, voice: str, output_dir: Path) -> Dict[str, Any]:
        """
        Synthesize multiple texts from a file without voice cloning.
        """
        try:
            # Import TextFileLoader
            from ..dataset.text_loaders import TextFileLoader

            self.logger.info(f"🎤 Starting batch synthesis with voice: {voice}")
            self.logger.info(f"📄 Loading texts from: {text_file}")
            self.logger.info(f"📁 Output directory: {output_dir}")

            # Load texts from file
            loader = TextFileLoader(text_file)
            text_items = loader.load()

            if not text_items:
                self.logger.error("❌ No texts loaded from file")
                return {'success': False, 'error': 'No texts loaded', 'processed': 0, 'failed': 0}

            self.logger.info(f"✅ Loaded {len(text_items)} texts for processing")

            # Setup driver and authenticate once
            if not self.driver:
                if not self.setup_driver():
                    return {'success': False, 'error': 'Failed to setup driver', 'processed': 0, 'failed': len(text_items)}

            if not self.navigate_to_base_url():
                return {'success': False, 'error': 'Failed to navigate to MiniMax', 'processed': 0, 'failed': len(text_items)}

            if not self.is_authenticated:
                if not self.authenticate():
                    self.logger.error("❌ Authentication failed")
                    return {'success': False, 'error': 'Authentication failed', 'processed': 0, 'failed': len(text_items)}

            # Process each text
            results = []
            processed = 0
            failed = 0

            for text_id, text in text_items:
                try:
                    self.logger.info(f"🎤 Processing text {processed + 1}/{len(text_items)}: {text_id}")

                    # Generate output filename
                    safe_id = "".join(c for c in text_id if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    output_file = output_dir / f"minimax_{safe_id}.wav"

                    # Generate voice without reference audio
                    success, audio_url = self.generate_voice(text)

                    if success and audio_url:
                        # Download audio
                        if self.download_audio(audio_url, output_file):
                            results.append({
                                'id': text_id,
                                'text': text,
                                'output_file': str(output_file),
                                'success': True,
                                'audio_url': audio_url
                            })
                            processed += 1
                            self.logger.info(f"✅ Generated: {output_file}")
                        else:
                            results.append({
                                'id': text_id,
                                'text': text,
                                'output_file': str(output_file),
                                'success': False,
                                'error': 'Download failed'
                            })
                            failed += 1
                            self.logger.error(f"❌ Download failed: {output_file}")
                    else:
                        results.append({
                            'id': text_id,
                            'text': text,
                            'output_file': str(output_file),
                            'success': False,
                            'error': 'Generation failed'
                        })
                        failed += 1
                        self.logger.error(f"❌ Generation failed: {text_id}")

                    # Brief pause between requests
                    import time
                    time.sleep(2)

                except Exception as e:
                    results.append({
                        'id': text_id,
                        'text': text,
                        'output_file': str(output_dir / f"minimax_{text_id}.wav"),
                        'success': False,
                        'error': str(e)
                    })
                    failed += 1
                    self.logger.error(f"❌ Error processing {text_id}: {e}")

            # Summary
            success_rate = processed / len(text_items) * 100 if text_items else 0

            batch_result = {
                'success': failed == 0,
                'total_texts': len(text_items),
                'processed': processed,
                'failed': failed,
                'success_rate': success_rate,
                'results': results,
                'voice': voice,
                'output_directory': str(output_dir)
            }

            self.logger.info(f"📊 Batch processing complete: {processed}/{len(text_items)} successful ({success_rate:.1f}%)")

            return batch_result

        except Exception as e:
            self.logger.error(f"❌ Batch synthesis error: {e}")
            self.take_screenshot("minimax_batch_synthesis_error.png")
            return {'success': False, 'error': str(e), 'processed': 0, 'failed': 0}

        finally:
            self.cleanup()

    def clone(self, text: str, reference_audio: Path, output_file: Path) -> bool:
        """
        Clone voice from reference audio and synthesize text.
        This is the main method for MiniMax voice cloning.
        """
        try:
            self.logger.info(f"🎭 Starting voice cloning with reference: {reference_audio}")

            # Setup driver and authenticate
            if not self.driver:
                if not self.setup_driver():
                    return False

            if not self.navigate_to_base_url():
                return False

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
            self.take_screenshot("minimax_cloning_error.png")
            return False

        finally:
            self.cleanup()
