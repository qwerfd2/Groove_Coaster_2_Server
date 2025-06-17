import os
import subprocess
from pathlib import Path

INPUT_DIR = Path("audio")
OUTPUT_DIR = Path("audio_shifted")
OUTPUT_DIR.mkdir(exist_ok=True)

def shift_audio(file_path: Path):
    output_file = OUTPUT_DIR / file_path.name
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", "0.02321",
        "-i", str(file_path),
        "-c", "copy",
        str(output_file)
    ]
    print(f"Processing {file_path.name}...")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    for file in INPUT_DIR.glob("*.m4a"):
        shift_audio(file)

if __name__ == "__main__":
    main()
