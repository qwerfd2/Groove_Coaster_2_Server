import struct
import openpyxl

def write_uvdata(input_excel, output_file):
    wb = openpyxl.load_workbook(input_excel)
    ws = wb.active
    
    sections = []
    for row in ws.iter_rows(values_only=True):
        if row[0]:
            sections.append(bytes.fromhex(row[0]))
    
    num_sections = len(sections)
    offsets = []
    current_offset = 6 + num_sections * 4 + 4 # Additional header repeat
    
    for section in sections:
        offsets.append(current_offset)
        current_offset += len(section)
    
    with open(output_file, 'wb') as f:
        file_length = struct.pack('>I', current_offset)
        num_sections_packed = struct.pack('>H', num_sections)
        f.write(file_length + num_sections_packed)

        for offset in offsets:
            f.write(struct.pack('>I', offset))
        
        f.write(file_length)
        
        for section in sections:
            f.write(section)
    
    print(f"Packed {num_sections} sections into {output_file}")

write_uvdata('uvdata.xlsx', 'out_uvdata.dat')