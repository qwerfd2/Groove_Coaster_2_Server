import os
import json

base_dir = os.getcwd()

stage_folder = os.path.join(base_dir, "stage")
stage_files = [f for f in os.listdir(stage_folder) if os.path.isfile(os.path.join(stage_folder, f))]

with open("download_manifest.json", "w", encoding="utf-8") as f:
    json.dump(stage_files, f, ensure_ascii=False, indent=2)

audio_folder = os.path.join(base_dir, "audio")
ogg_zip_files = [f for f in os.listdir(audio_folder) if f.endswith(".ogg.zip") and os.path.isfile(os.path.join(audio_folder, f))]

with open("download_manifest_android.json", "w", encoding="utf-8") as f:
    json.dump(ogg_zip_files, f, ensure_ascii=False, indent=2)

m4a_zip_files = [f for f in os.listdir(audio_folder) if f.endswith(".m4a.zip") and os.path.isfile(os.path.join(audio_folder, f))]

with open("download_manifest_ios.json", "w", encoding="utf-8") as f:
    json.dump(m4a_zip_files, f, ensure_ascii=False, indent=2)