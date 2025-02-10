def hex_to_json(hex_string):
    hex_string = hex_string.replace(" ", "").replace("\n", "")
    byte_data = bytes.fromhex(hex_string)
    
    if len(byte_data) % 4 != 0:
        raise ValueError("Hex data must contain a multiple of 4 bytes.")
    
    coordinates = []
    for i in range(0, len(byte_data), 4):
        x = int.from_bytes(byte_data[i:i+2], byteorder='big', signed=False)
        y = int.from_bytes(byte_data[i+2:i+4], byteorder='big', signed=False)
        coordinates.append({"x": x, "y": y})
    
    return coordinates

hex_data = input("Input the hex data (with header 8 bytes removed):")
json_output = hex_to_json(hex_data)
print(json_output)
