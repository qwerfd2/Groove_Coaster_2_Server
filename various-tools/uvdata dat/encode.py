import json

def json_to_hex(json_filename):
    with open(json_filename, 'r') as f:
        coordinates = json.load(f)
    
    hex_data = bytearray()
    
    for coord in coordinates:
        x_bytes = coord["x"].to_bytes(2, byteorder='big', signed=False)
        y_bytes = coord["y"].to_bytes(2, byteorder='big', signed=False)
        hex_data.extend(x_bytes + y_bytes)
    
    return hex_data.hex().upper()

file_name = input("input the json file name: ")

hex_output = json_to_hex(file_name)
print(hex_output)