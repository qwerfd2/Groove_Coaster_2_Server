import os
import json
import zlib

base_dir = os.getcwd()

def file_crc32(filepath):
    with open(filepath, "rb") as f:
        return zlib.crc32(f.read())

# 1. Stage files
stage_folder = os.path.join(base_dir, "stage")
stage_files = {
    f: file_crc32(os.path.join(stage_folder, f))
    for f in os.listdir(stage_folder)
    if os.path.isfile(os.path.join(stage_folder, f))
}

with open("download_manifest.json", "w", encoding="utf-8") as f:
    json.dump(stage_files, f, ensure_ascii=False, indent=2)

# 2. Android audio files (.ogg.zip)
audio_folder = os.path.join(base_dir, "audio")
ogg_zip_files = {
    f: file_crc32(os.path.join(audio_folder, f))
    for f in os.listdir(audio_folder)
    if f.endswith(".ogg.zip") and os.path.isfile(os.path.join(audio_folder, f))
}

with open("download_manifest_android.json", "w", encoding="utf-8") as f:
    json.dump(ogg_zip_files, f, ensure_ascii=False, indent=2)

# 3. iOS audio files (.m4a.zip)
m4a_zip_files = {
    f: file_crc32(os.path.join(audio_folder, f))
    for f in os.listdir(audio_folder)
    if f.endswith(".m4a.zip") and os.path.isfile(os.path.join(audio_folder, f))
}

with open("download_manifest_ios.json", "w", encoding="utf-8") as f:
    json.dump(m4a_zip_files, f, ensure_ascii=False, indent=2)