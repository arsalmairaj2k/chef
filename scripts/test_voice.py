"""
Chef AI — Groq Whisper Voice Integration Test Script
Usage:
    python scripts/test_voice.py
    python scripts/test_voice.py --mock
    python scripts/test_voice.py --file path/to/audio.wav
    python scripts/test_voice.py --key gsk_your_key_here
"""

import os
import sys
import argparse
import io
import wave
import math
import struct
from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()


def generate_synthetic_audio() -> bytes:
    """Generate a 1-second 440Hz sine wave WAV file in memory."""
    buf = io.BytesIO()
    sample_rate = 16000
    duration = 1.0  # seconds
    frequency = 440.0
    num_samples = int(sample_rate * duration)

    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            data = struct.pack("<h", value)
            wav_file.writeframes(data)

    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Test Groq Whisper Speech-to-Text for Chef AI")
    parser.add_argument("--file", help="Path to an existing audio file (WAV, MP3, M4A, WEBM)")
    parser.add_argument("--key", help="Groq API key (defaults to GROQ_API_KEY from environment)")
    parser.add_argument("--mock", action="store_true", help="Run in offline mock mode without calling external Groq API")
    args = parser.parse_args()

    api_key = args.key or os.getenv("GROQ_API_KEY")

    print("\n" + "=" * 60)
    print(" 🎙️  CHEF AI — GROQ WHISPER STT TEST SUITE")
    print("=" * 60)

    if not api_key and not args.mock:
        print("\n⚠️  Notice: GROQ_API_KEY is not set.")
        print("To enable live Groq Whisper transcription:")
        print("  1. Go to https://console.groq.com and sign up for free.")
        print("  2. Create an API key under 'API Keys'.")
        print("  3. Add it to your .env file: GROQ_API_KEY=gsk_your_key_here")
        print("  4. Or run this script with: python scripts/test_voice.py --key gsk_...")
        print("  5. Or run offline verification: python scripts/test_voice.py --mock\n")
        sys.exit(0)

    if args.mock:
        os.environ["APP_ENV"] = "test"
        from app.core.config import get_settings
        get_settings.cache_clear()
        print("\n🧪 Mock mode active (verifying pipeline without calling external Groq API)...")

    try:
        from app.services.audio_service import AudioTranscriptionService

        if args.file:
            if not os.path.exists(args.file):
                print(f"❌ Error: File not found at '{args.file}'")
                sys.exit(1)
            with open(args.file, "rb") as f:
                audio_bytes = f.read()
            filename = os.path.basename(args.file)
            print(f"📁 Loaded audio file: {filename} ({len(audio_bytes)} bytes)")
        else:
            print("🔊 Generating synthetic test audio snippet (1 sec, 16kHz WAV)...")
            audio_bytes = generate_synthetic_audio()
            filename = "synthetic_test.wav"

        print("⚡ Sending to Groq Whisper (model: whisper-large-v3)...")
        transcription = AudioTranscriptionService.transcribe(
            file_bytes=audio_bytes,
            filename=filename,
            api_key=api_key if not args.mock else None,
        )

        print("\n" + "-" * 60)
        print("✅ TRANSCRIPTION RESULT:")
        print(f"   \"{transcription}\"")
        print("-" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Transcription failed: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
