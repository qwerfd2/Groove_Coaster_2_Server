import struct
import json

def read_string(f):
    length = struct.unpack("B", f.read(1))[0]
    return f.read(length).decode("utf-8")

def read_int(f, size=2):
    return int.from_bytes(f.read(size), byteorder="big")

def read_list_of_ints(f):
    levels = []
    for _ in range(6):
        levels.append(struct.unpack('B', f.read(1))[0])
    return levels

def read_hex_string(f, size):
    return " ".join(f"{b:02X}" for b in f.read(size))

def read_flag_list(f):
    byte = f.read(1)[0]
    return [(byte >> i) & 1 for i in range(7, -1, -1)]

def parse_stage_param(file_path):
    with open(file_path, "rb") as f:
        num_elements = read_int(f, 2)
        print(num_elements)
        data = []
        for _ in range(num_elements):
            element = {
                "name_ja": read_string(f),
                "name_en": read_string(f),
                "image_id": read_int(f),
                "artist_ja": read_string(f),
                "artist_en": read_string(f),
                "length": read_string(f),
                "difficulty": read_list_of_ints(f),
                "bpm": read_string(f),
                "sample_name": read_string(f),
                "stage_id": read_string(f),
                "dd": f.read(2).decode("utf-8"),
                "ver": read_int(f, 1),
                "easy_name": read_string(f),
                "normal_name": read_string(f),
                "hard_name": read_string(f),
                "adlib_max_easy": read_int(f, 4),
                "adlib_max_normal": read_int(f, 4),
                "adlib_max_hard": read_int(f, 4),
                "no_adlib_max_easy": read_int(f, 4),
                "no_adlib_max_normal": read_int(f, 4),
                "no_adlib_max_hard": read_int(f, 4),
                "field_1": read_hex_string(f, 4),
                "padding_1": read_hex_string(f, 11),
                "flag_1": read_flag_list(f),
                "padding_2": read_hex_string(f, 5)
            }
            data.append(element)

    with open("stage_param.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

parse_stage_param("stage_param.dat")