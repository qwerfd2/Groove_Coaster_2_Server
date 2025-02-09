import struct
import openpyxl

def read_uvdata(file_path, output_excel):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    num_sections = struct.unpack('>H', data[4:6])[0]
    
    offsets = [struct.unpack('>I', data[6 + i * 4:10 + i * 4])[0] for i in range(num_sections)]
    offsets.append(len(data))
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    for i in range(num_sections):
        start, end = offsets[i], offsets[i + 1]
        section_data = data[start:end]
        hex_string = ' '.join(f'{byte:02X}' for byte in section_data)
        ws.append([hex_string])
    
    wb.save(output_excel)
    print(f"Extracted {num_sections} sections to {output_excel}")

read_uvdata('uvdata.dat', 'uvdata.xlsx')