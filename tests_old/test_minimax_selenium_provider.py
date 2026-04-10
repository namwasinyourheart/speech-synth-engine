#!/usr/bin/env python3
# ============================================================
# MiniMax Selenium Provider Test
# Test for MiniMax TTS provider with Selenium automation
# ============================================================

import sys
import logging
import os
from pathlib import Path

# Add speech-synth-engine to path
# sys.path.insert(0, "/home/nampv1/projects/tts/speech-synth-engine")

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []

    try:
        import selenium
    except ImportError:
        missing_deps.append("selenium")

    try:
        # Try to import undetected_chromedriver
        import undetected_chromedriver as uc
    except ImportError:
        print("⚠️  Warning: undetected_chromedriver not found. Install with: pip install undetected-chromedriver")
        try:
            from selenium import webdriver
        except ImportError:
            missing_deps.append("selenium")

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install selenium undetected-chromedriver")
        return False

    print("✅ All dependencies available")
    return True

def test_minimax_provider_initialization():
    """Test MiniMax provider initialization and configuration"""
    print("\n🧪 Testing MiniMax Provider Initialization...")

    try:
        from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

        # Test configuration
        config = {
            "base_url": "https://www.minimax.io/audio/voices-cloning",
            "google_email": os.getenv("MINIMAX_GOOGLE_EMAIL", ""),
            "google_password": os.getenv("MINIMAX_GOOGLE_PASSWORD", ""),
            "headless": False,
            "sample_rate": 22050,
            "language": "Vietnamese",
            "timeout": 30,
            "download_timeout": 120,
            "max_wait_time": 300
        }

        provider = MiniMaxSeleniumProvider("minimax_selenium", config)

        # Check provider info
        print(f"✅ Provider name: {provider.name}")
        print(f"✅ Supported voices: {provider.supported_voices}")
        print(f"✅ Language: {provider.language}")
        print(f"✅ Sample rate: {provider.sample_rate}")
        print(f"✅ Base URL: {provider.base_url}")
        print(f"✅ Headless mode: {provider.headless}")

        return True

    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        return False

def test_minimax_provider_metadata():
    """Test MiniMax provider metadata functionality"""
    print("\n🧪 Testing MiniMax Provider Metadata...")

    try:
        from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

        config = {"language": "Vietnamese", "sample_rate": 22050}
        provider = MiniMaxSeleniumProvider("minimax_selenium", config)

        # Test metadata info
        metadata = provider.get_metadata_info()
        print(f"✅ Provider metadata: {metadata}")

        # Test text validation
        test_cases = [
            ("Hello world", True),
            ("", False),
            ("   ", False),
            (None, False)
        ]

        for text, expected in test_cases:
            result = provider.validate_text(text)
            status = "✅" if result == expected else "❌"
            print(f"{status} Text validation '{text}': {result}")

        # Test duration estimation
        test_text = "Đây là một câu test để kiểm tra duration estimation"
        duration = provider.estimate_duration(test_text)
        print(f"✅ Estimated duration for '{test_text[:30]}...': {duration:.2f}s")

        return True

    except Exception as e:
        print(f"❌ Metadata test failed: {e}")
        return False

def test_minimax_provider_synthesis_dry_run():
    """Test MiniMax provider synthesis (dry run without actual Selenium)"""
    print("\n🧪 Testing MiniMax Provider Synthesis (Dry Run)...")

    try:
        from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

        config = {
            "base_url": "https://www.minimax.io/audio/voices-cloning",
            "google_email": "test@example.com",
            "google_password": "test_password",
            "headless": True,  # Use headless for testing
            "sample_rate": 22050,
            "language": "Vietnamese"
        }

        provider = MiniMaxSeleniumProvider("minimax_selenium", config)

        # Test synthesis with metadata (without actual Selenium execution)
        test_text = "Đây là test MiniMax provider"
        output_file = Path("test_output/minimax_test_dry_run.wav")

        # Create output directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Test the synthesis_with_metadata method
        result = provider.synthesize_with_metadata(test_text, "cloned_voice", output_file)

        print(f"✅ Synthesis result: {result}")

        # Check if result structure is correct
        required_keys = ['success', 'text', 'voice', 'output_file', 'provider', 'error']
        missing_keys = [key for key in required_keys if key not in result]

        if missing_keys:
            print(f"❌ Missing keys in result: {missing_keys}")
            return False

        print("✅ All required keys present in result")
        return True

    except Exception as e:
        print(f"❌ Synthesis dry run test failed: {e}")
        return False

def test_minimax_with_real_selenium():
    """Test MiniMax provider with real Selenium (requires credentials)"""
    print("\n🧪 Testing MiniMax Provider with Real Selenium...")

    # Check if credentials are available
    google_email = os.getenv("MINIMAX_GOOGLE_EMAIL", "signupwithnamm@gmail.com")
    google_password = os.getenv("MINIMAX_GOOGLE_PASSWORD", "mailthanhthuy667")

    if not google_email or not google_password:
        print("⚠️  Skipping real Selenium test - credentials not configured")
        print("Set MINIMAX_GOOGLE_EMAIL and MINIMAX_GOOGLE_PASSWORD environment variables")
        return True

    try:
        from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

        config = {
            "base_url": "https://www.minimax.io/audio/voices-cloning",
            "google_email": google_email,
            "google_password": google_password,
            "headless": False,  # Use non-headless for debugging
            "sample_rate": 22050,
            "language": "Vietnamese",
            "timeout": 60,
            "download_timeout": 180,
            "max_wait_time": 300
        }

        provider = MiniMaxSeleniumProvider("minimax_selenium", config)

        # Test with reference audio (check if valid audio file exists)
        reference_audio = Path("test_output/sample_reference.wav")
        reference_audio.parent.mkdir(parents=True, exist_ok=True)

        # Check if we have a valid reference audio file
        valid_reference_sources = [
            Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/audio/test.wav"),
            Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/gtss_test.wav"),
            Path("/home/nampv1/projects/tts/tts-ft/test_output/audio/generated_voice_1.wav"),
            Path("/media/nampv1/hdd/data/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10-20251024T103708Z-1-001/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10/spk2_1.m4a")
        ]

        valid_reference = None
        for source in valid_reference_sources:
            if source.exists() and source.stat().st_size > 1000:  # At least 1KB
                valid_reference = source
                break

        if not valid_reference:
            print("⚠️ No valid reference audio found for testing")
            print("⚠️ Skipping real MiniMax voice cloning test")
            print("ℹ️ To test with real voice cloning:")
            print("   1. Place a valid audio file (.wav/.mp3) in test_output/ directory")
            print("   2. Or set MINIMAX_REFERENCE_AUDIO environment variable")
            print("   3. Run test again")
            return True

        # Copy the valid reference audio for testing
        import shutil
        shutil.copy(valid_reference, reference_audio)
        print(f"✅ Using valid reference audio: {valid_reference} -> {reference_audio}")
        print(f"📊 Reference audio size: {reference_audio.stat().st_size / 1024:.1f} KB")

        test_text = "Đây là test với MiniMax voice cloning"
        output_file = Path("test_output/minimax_real_test.wav")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"🎤 Testing synthesis with text: {test_text}")
        print(f"📁 Output file: {output_file}")
        print(f"🎵 Reference audio: {reference_audio}")
        print(f"📊 Reference audio size: {reference_audio.stat().st_size / 1024:.1f} KB")

        # Test cloning with reference audio
        start_time = time.time()
        success = provider.clone(test_text, reference_audio, output_file)
        end_time = time.time()

        if success and output_file.exists():
            file_size = output_file.stat().st_size
            duration = end_time - start_time
            print("✅ Real synthesis successful!")
            print(f"📊 File size: {file_size / 1024:.1f} KB")
            print(f"⏱️  Duration: {duration:.1f}s")
            return True
        else:
            print("❌ Real synthesis failed")
            print(f"📊 File exists: {output_file.exists()}")
            print(f"📊 File size: {output_file.stat().st_size if output_file.exists() else 0} bytes")
            return False

    except Exception as e:
        print(f"❌ Real Selenium test failed: {e}")
        return False

def test_minimax_batch_processing():
    """Test MiniMax batch processing functionality"""
    print("\n🧪 Testing MiniMax Batch Processing...")

    # Check if credentials are available
    google_email = os.getenv("MINIMAX_GOOGLE_EMAIL", "signupwithnamm@gmail.com")
    google_password = os.getenv("MINIMAX_GOOGLE_PASSWORD", "mailthanhthuy667")

    if not google_email or not google_password:
        print("⚠️  Skipping batch test - credentials not configured")
        return True

    try:
        from speech_synth_engine.providers.minimax_selenium_provider import MiniMaxSeleniumProvider

        config = {
            "base_url": "https://www.minimax.io/audio/voices-cloning",
            "google_email": google_email,
            "google_password": google_password,
            "headless": False,
            "sample_rate": 22050,
            "language": "Vietnamese",
            "timeout": 60,
            "download_timeout": 180,
            "max_wait_time": 300
        }

        provider = MiniMaxSeleniumProvider("minimax_selenium", config)

        # Create a sample text file for batch processing
        text_file = Path("test_output/sample_texts.txt")
        text_file.parent.mkdir(parents=True, exist_ok=True)

        sample_texts = [
            "1\tXin chào, đây là text đầu tiên",
            "2\tText thứ hai để test",
            "3\tCâu cuối cùng trong batch test"
        ]

        text_file.write_text("\n".join(sample_texts), encoding='utf-8')
        print(f"✅ Created sample text file: {text_file}")

        # Check if we have a valid reference audio file for batch processing
        valid_reference_sources = [
            Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/audio/test.wav"),
            Path("/home/nampv1/projects/tts/speech-synth-engine/test_output/gtss_test.wav"),
            Path("/home/nampv1/projects/tts/tts-ft/test_output/audio/generated_voice_1.wav"),
            Path("/media/nampv1/hdd/data/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10-20251024T103708Z-1-001/mẫu-giọng-nhân-viên-nhập-liệu-bưu-cục-thăng-long-24-10/spk2_1.m4a")
        ]

        valid_reference = None
        for source in valid_reference_sources:
            if source.exists() and source.stat().st_size > 1000:  # At least 1KB
                valid_reference = source
                break

        if not valid_reference:
            print("⚠️ No valid reference audio found for batch testing")
            print("⚠️ Skipping clone_batch test")
            return True

        # Test batch processing with reference audio
        output_dir = Path("test_output/minimax_batch")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy the valid reference audio for testing
        import shutil
        batch_reference_audio = Path("test_output/batch_reference.wav")
        shutil.copy(valid_reference, batch_reference_audio)
        print(f"✅ Using valid reference audio: {valid_reference} -> {batch_reference_audio}")
        print(f"📊 Reference audio size: {batch_reference_audio.stat().st_size / 1024:.1f} KB")

        print("🧪 Testing clone_batch...")
        result = provider.clone_batch(text_file, batch_reference_audio, output_dir)

        print(f"📊 Batch cloning result: {result}")
        print(f"✅ Texts loaded: {result.get('total_texts', 0)}")
        print(f"✅ Success rate: {result.get('success_rate', 0):.1f}%")

        # Clean up
        if text_file.exists():
            text_file.unlink()
        if batch_reference_audio.exists():
            batch_reference_audio.unlink()

        return True

    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting MiniMax Selenium Provider Tests...")
    print("=" * 60)

    setup_logging()

    if not check_dependencies():
        return False

    tests = [
        # test_minimax_provider_initialization,
        # test_minimax_provider_metadata,
        # test_minimax_provider_synthesis_dry_run,
        # test_minimax_with_real_selenium,
        test_minimax_batch_processing
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED")
            else:
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")

        print("-" * 40)

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    import time
    success = main()
    sys.exit(0 if success else 1)
