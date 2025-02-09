import struct
import pandas as pd

def read_string(f):
    length = struct.unpack("B", f.read(1))[0]
    str = f.read(length).decode("utf-8")
    print("str ", str)
    return str

def read_int_old(f, size=4):
    integer = int.from_bytes(f.read(size), byteorder="big")
    return integer

def read_int(f, size=4):
    result = " ".join(f"{b:02X}" for b in f.read(size))
    print("int ", result)
    return result

def read_byte(f):
    result = " ".join(f"{b:02X}" for b in f.read(1))
    print("byte ", result)
    return result

def parse_pak_file(file_path, output_xlsx):
    with open(file_path, "rb") as f:
        num_elements = read_int_old(f, 2)
        data = []
        
        for _ in range(num_elements):
            print("prd", _)
            entry = {
                "Field1": read_int(f),
                "Field2": read_byte(f),
                "Field3": read_int(f),
                "Field4": read_byte(f),
                "String1": read_string(f),
                "String2": read_string(f),
                "String3": read_string(f),
                "String4": read_string(f),
                "String5": read_string(f),
                "String6": read_string(f),
                "Field5": read_int(f),
                "Float1": read_int(f, 1),
                "Float2": read_int(f, 1),
                "Float3": read_int(f, 1),
                "Float4": read_int(f, 1),
                "Field6": read_byte(f),
                "Field7": read_byte(f),
                "Field8": read_int(f),
                "Field9": read_byte(f),
                "Field10": read_byte(f),
                "Field11": read_int(f),
                "Field12": read_int(f),
                "Field13": read_int(f),
                "Field14": read_int(f),
                "Field15": read_byte(f),
                "Field16": read_byte(f),
                "Field17": read_int(f),
                "Field18": read_int(f),
                "Field19": read_byte(f),
                "Field20": read_int(f),
                "Field21": read_byte(f),
                "Field22": read_int(f),
                "Field23": read_int(f),
                "Field24": read_byte(f),
                "Field25": read_int(f),
                "Field26": read_int(f),
                "Field27": read_byte(f),
                "Field28": read_int(f),
                "Field29": read_int(f),
                "Field30": read_byte(f),
                "Field31": read_int(f),
                "Field32": read_int(f),
                "Field33": read_int(f),
                "Field34": read_byte(f),
                "Field35": read_int(f),
                "Field36": read_int(f),
                "Field37": read_int(f),
                "Field38": read_byte(f)
            }
            # This is a hack (not derived from IDA) but there are discrepancies here that can be addressed this way
            if (entry["String5"] != "" or entry["String6"] != "" ):
                entry["Field39"] = read_int(f)
            
            entry["Field40"] = read_byte(f)
            data.append(entry)

    df = pd.DataFrame(data)
    df.to_excel(output_xlsx, index=False)

# Example usage
parse_pak_file("player.dat", "player.xlsx")
