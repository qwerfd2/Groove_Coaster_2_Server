import struct
import json
import os

FILES = {
    "player_name_en.json": "player_name_en.dat",
    "player_name_ja.json": "player_name_ja.dat",
    "player_name_it.json": "player_name_it.dat",
    "player_name_fr.json": "player_name_fr.dat"
}

def parse_hex_string(hex_string):
    return bytes.fromhex(hex_string)

def pack_sysmes(input_json, output_filename):
    with open(input_json, 'r', encoding='utf-8') as json_file:
        strings = json.load(json_file)

    with open(output_filename, 'wb') as f:
        f.write(struct.pack('>H', len(strings)))

        for string in strings:
            encoded_string = string.encode('utf-8')
            f.write(struct.pack('>H', len(encoded_string)))
            f.write(encoded_string)

if __name__ == "__main__":
    for json_file, dat_file in FILES.items():
        if os.path.exists(json_file):
            print(f"Processing {json_file} → {dat_file}")
            pack_sysmes(json_file, dat_file)
        else:
            print(f"Warning: {json_file} not found, skipped.")
