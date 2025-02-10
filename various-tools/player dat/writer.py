import struct
import pandas as pd

def write_string(f, s):
    if pd.isna(s):
        f.write(struct.pack("B", 0))
    else:
        encoded = s.encode("utf-8")
        f.write(struct.pack("B", len(encoded)))
        f.write(encoded)

def write_int(f, value, size=4):
    f.write(bytes.fromhex(value))

def write_byte(f, value):
    if pd.isna(value):
        f.write(struct.pack("B", 0))
    else:
        f.write(bytes.fromhex(value))

def convert_xlsx_to_dat(input_xlsx, output_dat):
    df = pd.read_excel(input_xlsx, dtype=str)
    
    with open(output_dat, "wb") as f:
        num_elements = len(df)
        write_int(f, f"{num_elements:04X}", 2)
        
        for _, row in df.iterrows():
            write_int(f, row["Field1"])
            write_byte(f, row["Field2"])
            write_int(f, row["Field3"])
            write_byte(f, row["Field4"])
            write_string(f, row["String1"])
            write_string(f, row["String2"])
            write_string(f, row["String3"])
            write_string(f, row["String4"])
            write_string(f, row["String5"])
            write_string(f, row["String6"])
            write_int(f, row["Field5"])
            write_byte(f, row["Field7"])
            write_int(f, row["Field8"])
            write_byte(f, row["Field9"])
            write_byte(f, row["Field10"])
            write_int(f, row["Field11"])
            write_int(f, row["Field12"])
            write_int(f, row["Field13"])
            write_int(f, row["Field14"])
            write_byte(f, row["Field15"])
            write_byte(f, row["Field16"])
            write_int(f, row["Field17"])
            write_int(f, row["Field18"])
            write_byte(f, row["Field19"])
            write_int(f, row["Field20"])
            write_byte(f, row["Field21"])
            write_int(f, row["Field22"])
            write_int(f, row["Field23"])
            write_byte(f, row["Field24"])
            write_int(f, row["Field25"])
            write_int(f, row["Field26"])
            write_byte(f, row["Field27"])
            write_int(f, row["Field28"])
            write_int(f, row["Field29"])
            write_byte(f, row["Field30"])
            write_int(f, row["Field31"])
            write_int(f, row["Field32"])
            write_int(f, row["Field33"])
            write_byte(f, row["Field34"])
            write_int(f, row["Field35"])
            write_int(f, row["Field36"])
            write_int(f, row["Field37"])
            write_byte(f, row["Field38"])
            
convert_xlsx_to_dat("player.xlsx", "out_player.dat")