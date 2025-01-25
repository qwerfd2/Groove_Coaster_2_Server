import os
import struct

# Credit: QuickBMS script on unpacking the .pak file.
# Used the reverse logic to help implement the packing script also.

def unpack_pak(file_path, output_folder):
    with open(file_path, 'rb') as f:
        # Big-endian
        endian = '>'
        
        # Read headers
        pak_size = struct.unpack(endian + 'I', f.read(4))[0]
        info_size = struct.unpack(endian + 'I', f.read(4))[0]
        info_size_repeat = struct.unpack(endian + 'I', f.read(4))[0]
        assert info_size == info_size_repeat, "INFO_SIZE mismatch"
        
        zero_byte = struct.unpack(endian + 'B', f.read(1))[0]
        assert zero_byte == 0, "Expected zero byte"
        
        names_offset = f.tell()
        base_offset = names_offset + info_size
        
        # Get the number of files
        files_count = struct.unpack(endian + 'H', f.read(2))[0]
        
        name_offsets = []
        offsets = []
        sizes = []
        cur = 0

        # Acquire offset
        for _ in range(files_count + 1):
            cur += 1
            name_offset = struct.unpack(endian + 'I', f.read(4))[0]
            offset = struct.unpack(endian + 'I', f.read(4))[0]
            size = struct.unpack(endian + 'I', f.read(4))[0]
            if (cur <= files_count):
                zero_byte = struct.unpack(endian + 'B', f.read(1))[0]
                assert zero_byte == 0, "Expected zero byte in file metadata"
            
            name_offsets.append(name_offset)
            offsets.append(offset)
            sizes.append(size)
        
        # Extract files
        os.makedirs(output_folder, exist_ok=True)
        for i in range(files_count):
            name_offset = name_offsets[i]
            offset = offsets[i]
            size = sizes[i]
            
            name_size = name_offsets[i + 1] - name_offset
            
            f.seek(names_offset + name_offset)
            name = f.read(name_size).decode('utf-8').rstrip('\x00')
            
            f.seek(base_offset + offset)
            data = f.read(size)
            
            output_path = os.path.join(output_folder, name)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as out_file:
                out_file.write(data)
            print(f"Extracted: {name}")

# Main script
if __name__ == "__main__":
    pak_file = input("Enter the path to the .pak file: ").strip()
    extract_folder = input("Enter the folder to extract to: ").strip()
    
    if not os.path.isfile(pak_file):
        print("Error: The specified .pak file does not exist.")
    else:
        unpack_pak(pak_file, extract_folder)
        print("Extraction complete.")
