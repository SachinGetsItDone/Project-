"""
NVIDIA STS (Speech-to-Speech) / NIM / Riva Model Setup Script.

Features:
1. Installs Python packages with granular per-package error handling (compatible with Python 3.10-3.14).
2. Sets up NVIDIA NIM / Riva Speech-to-Speech API integration.
3. Tests both Cloud NVIDIA STS execution (via NVIDIA API key) and local STS engine.
"""

import sys
import os
import subprocess
import argparse

# Ensure standard UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

CORE_PACKAGES = [
    "httpx",
    "pydantic",
    "python-dotenv",
    "numpy",
    "soundfile"
]

OPTIONAL_ML_PACKAGES = [
    "torch",
    "torchaudio",
    "transformers",
    "accelerate",
    "huggingface_hub",
    "nvidia-riva-client"
]

def install_package(pkg_name: str) -> bool:
    """Attempts to install a single package via pip."""
    cmd = [sys.executable, "-m", "pip", "install", pkg_name]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  [+] Installed {pkg_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [-] Skipped {pkg_name} (Not available for Python {sys.version.split()[0]}: {e.stderr.strip()[:100]}...)")
        return False

def install_all_dependencies():
    """Installs required packages individually for maximum compatibility."""
    print("=" * 60)
    print(f"[*] Step 1: Installing Dependencies for Python {sys.version.split()[0]}...")
    print("=" * 60)
    
    print("Installing core runtime packages:")
    for pkg in CORE_PACKAGES:
        install_package(pkg)
        
    print("\nInstalling optional deep learning packages:")
    for pkg in OPTIONAL_ML_PACKAGES:
        install_package(pkg)
    print("\n[+] Dependency installation check finished.\n")

def test_nvidia_sts_gateway():
    """Validates the NVIDIA STS service."""
    print("=" * 60)
    print("[*] Step 2: Testing NVIDIA Speech-to-Speech (STS) Pipeline...")
    print("=" * 60)
    
    try:
        import asyncio
        from services.nvidia_sts_service import NVIDIASTSService
        
        sts = NVIDIASTSService()
        
        async def run_turn():
            return await sts.process_speech_turn(
                text_prompt="Explain distributed transactions and 2-phase commit.",
                context="Candidate interview round for Backend Engineer"
            )
            
        result = asyncio.run(run_turn())
        print(f"[+] User Transcript : {result.get('transcript')}")
        print(f"[+] AI Question/Text: {result.get('response_text')}")
        print(f"[+] Audio Synthesized: {len(result.get('audio_bytes', b''))} bytes")
        print(f"[+] STS Latency      : {result.get('latency_ms')} ms")
        print(f"[+] Engine / Model   : {result.get('model')}")
        print("\n" + "=" * 60)
        print("[SUCCESS] NVIDIA STS Model Engine is operational and ready!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"[!] Error during STS verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Install and setup NVIDIA STS Model Engine")
    parser.add_argument("--skip-pip", action="store_true", help="Skip pip installation step")
    args = parser.parse_args()

    if not args.skip_pip:
        install_all_dependencies()
        
    test_nvidia_sts_gateway()

if __name__ == "__main__":
    main()
