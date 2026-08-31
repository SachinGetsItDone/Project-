"""Backend setup helper: install dependencies, then smoke-test the STS service.

Run from the ``server/`` directory:

    python scripts/install_s2s_model.py            # install requirements + smoke test
    python scripts/install_s2s_model.py --skip-pip # smoke test only

Dependencies are defined once in ``server/requirements.txt`` (the single source
of truth); this script simply installs from there so the two never drift.
"""

import argparse
import asyncio
import os
import subprocess
import sys

# Make the server/ package root importable when run as a plain script.
SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SERVER_DIR)

# Ensure UTF-8 output on Windows consoles.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def install_dependencies():
    req = os.path.join(SERVER_DIR, "requirements.txt")
    print(f"[*] Installing dependencies from {req} ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req], check=True)
    print("[+] Dependencies installed.\n")


def smoke_test_sts():
    print("[*] Smoke-testing the NVIDIA STS service ...")
    from services.nvidia_sts_service import NVIDIASTSService

    async def run_turn():
        sts = NVIDIASTSService()
        return await sts.process_speech_turn(
            text_prompt="Explain distributed transactions and 2-phase commit.",
            context="Candidate interview round for Backend Engineer",
        )

    result = asyncio.run(run_turn())
    print(f"[+] Transcript     : {result.get('transcript')}")
    print(f"[+] Response text  : {result.get('response_text')}")
    print(f"[+] Audio bytes    : {len(result.get('audio_bytes', b''))}")
    print(f"[+] Latency (ms)   : {result.get('latency_ms')}")
    print(f"[+] Model / engine : {result.get('model')}")
    print("[SUCCESS] NVIDIA STS service is operational.")


def main():
    parser = argparse.ArgumentParser(description="Install deps and smoke-test the STS service.")
    parser.add_argument("--skip-pip", action="store_true", help="Skip dependency installation.")
    args = parser.parse_args()

    if not args.skip_pip:
        install_dependencies()
    smoke_test_sts()


if __name__ == "__main__":
    main()
