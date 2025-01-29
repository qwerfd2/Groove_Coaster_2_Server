import json
import struct

def write_string(f, s):
    data = s.encode("utf-8")
    f.write(struct.pack("B", len(data)))
    f.write(data)

def write_int(f, value, size=2):
    f.write(value.to_bytes(size, byteorder="big"))

def write_list_of_ints(f, values):
    f.write(bytes(values))

def write_hex_string(f, hex_string):
    f.write(bytes.fromhex(hex_string))

def write_flag_list(f, flag_list):
    byte_value = sum((bit << (7 - i)) for i, bit in enumerate(flag_list))
    f.write(struct.pack("B", byte_value))

def convert_json_to_dat(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(output_path, "wb") as f:
        write_int(f, len(data), 2)

        for element in data:
            write_string(f, element["name_ja"])
            write_string(f, element["name_en"])
            write_int(f, element["image_id"], 2)
            write_string(f, element["artist_ja"])
            write_string(f, element["artist_en"])
            write_string(f, element["length"])
            write_list_of_ints(f, element["difficulty"])
            write_string(f, element["bpm"])
            write_string(f, element["sample_name"])
            write_string(f, element["stage_id"])
            
            f.write(element["dd"].encode("utf-8"))

            write_int(f, element["ver"], 1)
            write_string(f, element["easy_name"])
            write_string(f, element["normal_name"])
            write_string(f, element["hard_name"])
            
            write_int(f, element["adlib_max_easy"], 4)
            write_int(f, element["adlib_max_normal"], 4)
            write_int(f, element["adlib_max_hard"], 4)
            write_int(f, element["no_adlib_max_easy"], 4)
            write_int(f, element["no_adlib_max_normal"], 4)
            write_int(f, element["no_adlib_max_hard"], 4)

            write_hex_string(f, element["field_1"])
            write_hex_string(f, element["padding_1"])
            write_flag_list(f, element["flag_1"])
            write_hex_string(f, element["padding_2"])

convert_json_to_dat("stage_param.json", "out_stage_param.dat")