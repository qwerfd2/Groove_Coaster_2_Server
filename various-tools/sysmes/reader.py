import struct
import json

def unpack_sysmes(filename, output_json):
    with open(filename, 'rb') as f:
        num_elements = struct.unpack('>H', f.read(2))[0] - 1
        
        f.read(2)
        
        strings = []
        for _ in range(num_elements):
            str_length = struct.unpack('>H', f.read(2))[0]
            
            string_data = f.read(str_length)
            decoded_string = string_data.decode('utf-8', errors='replace')
            print(decoded_string)
            strings.append(decoded_string)
        
    with open(output_json, 'w', encoding='utf-8') as json_file:
        json.dump(strings, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    filename = "sysmes_it.dat"
    output_json = "sysmes_it.json"
    unpack_sysmes(filename, output_json)