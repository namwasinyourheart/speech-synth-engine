import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))

from speech_synth_engine.providers.vnpost_provider import VnPostTTSProvider

def test_vnpost_clone():
    """
    Test VnPostTTSProvider clone method.
    """
    # Khởi tạo provider
    provider = VnPostTTSProvider()

    # Test parameters
    text = "Xin chào, đây là giọng nói được clone từ reference audio của bạn."
    reference_audio = Path("test_audio/reference.wav")  # File reference audio cần tồn tại
    output_file = Path("test_output/vnpost_clone_test.wav")

    # Tạo thư mục nếu chưa có
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Kiểm tra file reference có tồn tại không
        if not reference_audio.exists():
            print(f"⚠️  File reference audio không tồn tại: {reference_audio}")
            print("Bạn cần tạo file reference audio để test clone functionality")
            return False

        # Gọi clone method
        provider.clone(
            text=text,
            reference_audio=reference_audio,
            output_file=output_file
        )

        # Kiểm tra file được tạo
        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✅ Clone thành công! File WAV được tạo: {output_file}")
            print(f"📊 Kích thước file: {file_size} bytes")
            return True
        else:
            print("❌ File clone không được tạo")
            return False

    except NotImplementedError as e:
        print(f"❌ Clone chưa được implement: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi test clone: {e}")
        return False

def test_gemini_no_clone():
    """
    Test GeminiTTSProvider không hỗ trợ clone.
    """
    from providers.gemini_provider import GeminiTTSProvider

    provider = GeminiTTSProvider()

    try:
        provider.clone(
            text="Test",
            reference_audio=Path("test.wav"),
            output_file=Path("test.wav")
        )
        print("❌ Gemini provider không nên hỗ trợ clone")
        return False
    except NotImplementedError:
        print("✅ Gemini provider đúng không hỗ trợ clone")
        return True
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Đang test clone functionality...")

    # Test VnPost clone (cần file reference audio)
    print("\n📋 Test VnPost Clone:")
    clone_success = test_vnpost_clone()

    # Test Gemini không hỗ trợ clone
    print("\n📋 Test Gemini không hỗ trợ clone:")
    gemini_success = test_gemini_no_clone()

    if clone_success and gemini_success:
        print("\n🎉 Tất cả clone tests thành công!")
    else:
        print("\n💥 Một số clone tests thất bại!")
        if not clone_success:
            print("💡 Bạn cần tạo file reference audio để test VnPost clone")
        sys.exit(1)
