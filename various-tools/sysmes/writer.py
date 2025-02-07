import struct
import json
import os

FILES = {
    "sysmes.json": "sysmes.dat",
    "sysmes_en.json": "sysmes_en.dat",
    "sysmes_fr.json": "sysmes_fr.dat",
    "sysmes_it.json": "sysmes_it.dat"
}

# Bodge - Not sure what tf is happening for the last string
APPEND_BYTES = {
    "sysmes.json": "",
    "sysmes_en.json": "AF E3 81 A7 E3 81 8D E3 81 BE E3 81 9B E3 82 93 E3 80 82 0A E3 82 A2 E3 82 AB E3 82 A6 E3 83 B3 E3 83 88 E3 82 92 E5 89 8A E9 99 A4 E3 81 97 E3 81 BE E3 81 99 E3 81 8B EF BC 9F 00 03 59 65 73 00 02 4E 6F 00 27 E3 82 A2 E3 82 AB E3 82 A6 E3 83 B3 E3 83 88 E3 82 92 E5 89 8A E9 99 A4 E3 81 97 E3 81 BE E3 81 97 E3 81 9F E3 80 82",
    "sysmes_fr.json": "61 20 C3 A9 74 C3 A9 20 73 75 70 70 72 69 6D C3 A9 2E",
    "sysmes_it.json": "83 88 E3 82 92 E5 89 8A E9 99 A4 E3 81 97 E3 81 BE E3 81 97 E3 81 9F E3 80 82"
}

def parse_hex_string(hex_string):
    return bytes.fromhex(hex_string)

def pack_sysmes(input_json, output_filename, append_bytes):
    with open(input_json, 'r', encoding='utf-8') as json_file:
        strings = json.load(json_file)

    with open(output_filename, 'wb') as f:
        f.write(struct.pack('>H', len(strings) + 1))  # Bodge, last string is fucced
        f.write(b'\x00\x00')

        for string in strings:
            encoded_string = string.encode('utf-8')
            f.write(struct.pack('>H', len(encoded_string)))
            f.write(encoded_string)

        f.write(parse_hex_string(append_bytes))

if __name__ == "__main__":
    for json_file, dat_file in FILES.items():
        if os.path.exists(json_file):
            print(f"Processing {json_file} → {dat_file}")
            pack_sysmes(json_file, dat_file, APPEND_BYTES[json_file])
        else:
            print(f"Warning: {json_file} not found, skipped.")
