"""
Test script for TTS Gateway API.

Usage:
    # Start the gateway first:
    PYTHONPATH=. python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
    
    # Then run tests:
    PYTHONPATH=. python gateway/test_gateway.py
    
    # Or use requests directly:
    curl -X POST http://localhost:8000/tts \
        -H "Content-Type: application/json" \
        -d '{"provider": "gtts", "text": "Xin chào"}'
"""
import requests
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("\n🩺 Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200


def test_list_providers():
    """Test list providers endpoint."""
    print("\n📋 Testing /providers endpoint...")
    response = requests.get(f"{BASE_URL}/providers")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Registered providers: {data.get('registered', [])}")
    print(f"Available types: {data.get('available_types', [])}")
    return response.status_code == 200


def test_provider_info(provider_name: str):
    """Test get provider info endpoint."""
    print(f"\nℹ️  Testing /providers/{provider_name} endpoint...")
    response = requests.get(f"{BASE_URL}/providers/{provider_name}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)[:500]}...")
    else:
        print(f"Error: {response.text}")
    return response.status_code == 200


def test_tts_gtts():
    """Test TTS synthesis with gTTS (should work without API keys)."""
    print("\n🔊 Testing POST /tts with gTTS...")
    
    payload = {
        "provider": "gtts",
        "text": "Xin chào, đây là giọng nói được tạo ra bởi Gateway.",
        "voice_config": {
            "voice_id": "vi",
            "language": "vi"
        },
        "audio_config": {
            "container": "wav",
            "sample_rate": 22050
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tts",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data.get("success"):
        print(f"✅ Audio file: {data.get('audio_url')}")
        return True
    else:
        print(f"❌ Synthesis failed: {data.get('error')}")
        return False


def test_tts_cartesia():
    """Test TTS synthesis with Cartesia (requires API key)."""
    print("\n🔊 Testing POST /tts with Cartesia...")
    
    payload = {
        "provider": "cartesia",
        "model": "sonic-3",
        "text": "Nhiều thông điệp quan trọng về vai trò của Quốc hội.",
        "voice_config": {
            "voice_id": "0e58d60a-2f1a-4252-81bd-3db6af45fb41",
            "language": "vi",
            "speed": 1.0,
            "emotion": "neutral"
        },
        "audio_config": {
            "container": "mp3",
            "encoding": "pcm_f32le",
            "sample_rate": 44100
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tts",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data.get("success"):
        print(f"✅ Audio file: {data.get('audio_url')}")
        return True
    else:
        print(f"❌ Synthesis failed: {data.get('error')}")
        return False


def test_tts_invalid_provider():
    """Test TTS with invalid provider."""
    print("\n🚫 Testing POST /tts with invalid provider...")
    
    payload = {
        "provider": "invalid_provider",
        "text": "Test text"
    }
    
    response = requests.post(
        f"{BASE_URL}/tts",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Should return 200 but with success=False (provider error, not gateway error)
    if not data.get("success") and data.get("error"):
        print("✅ Correctly returned error for invalid provider")
        return True
    return False


def test_docs():
    """Test auto-generated docs."""
    print("\n📚 Testing /docs endpoint...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {response.status_code}")
    return response.status_code == 200


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 TTS Gateway Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("List Providers", test_list_providers),
        ("Provider Info (gtts)", lambda: test_provider_info("gtts")),
        ("TTS with gTTS", test_tts_gtts),
        ("TTS with Cartesia", test_tts_cartesia),
        ("TTS Invalid Provider", test_tts_invalid_provider),
        ("API Docs", test_docs),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test '{name}' failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
