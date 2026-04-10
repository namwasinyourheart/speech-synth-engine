def _calculate_duration(audio_path: str) -> float:
        """
        Calculate audio duration using soundfile.

        Args:
            audio_path: Path to the audio file (e.g., .wav)

        Returns:
            Duration in seconds as float. Returns 0.0 if duration can't be determined.
        """
        try:
            import soundfile as sf  # lazy import to avoid hard dep at module import time
            with sf.SoundFile(str(audio_path)) as f:
                frames = len(f)
                sr = int(f.samplerate) if getattr(f, 'samplerate', 0) else 0
                return round(frames / sr, 3) if sr > 0 else 0.0
        except Exception as e:
            self.logger.warning(f"⚠️  Could not determine duration for {audio_path}: {e}")
            return 0.0

if __name__ == "__main__":
    audio_path = "/home/nampv1/projects/tts/speech-synth-engine/test_output/test_generator_gemini/20260406_111553/gemini/gemini-2.5-flash-preview-tts/Zephyr/wav/0106688805_xóm_bảy,_thôn_phương_khê,_xã_phú_phương,_huyện_ba.wav"
    duration = _calculate_duration(audio_path)
    print(duration)
