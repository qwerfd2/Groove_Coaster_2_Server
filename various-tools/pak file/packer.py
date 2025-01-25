import os
import struct
import math

def pack_pak(input_folder, output_file):
    with open(output_file, 'wb') as f:
        # Big-endian
        endian = '>'
        
        # Prepare file metadata
        files = []
        for root, _, filenames in os.walk(input_folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, input_folder).replace("\\", "/")
                files.append((relative_path, file_path))
        
        files.sort(key=lambda x: x[0])  # Sort files (this is actually necessary)
        
        # Write header placeholder
        f.write(b'\x00' * 4)  # PAK_SIZE
        f.write(b'\x00' * 4)  # INFO_SIZE
        f.write(b'\x00' * 4)  # INFO_SIZE repeat
        f.write(struct.pack(endian + 'B', 0))  # ZERO byte
        
        # Write number of files
        f.write(struct.pack(endian + 'H', len(files)))  # FILES
        
        # Calculate offsets
        header_size = 16  # Fixed header size
        metadata_size = len(files) * 13 + 2  # Metadata for all files + FILES field
        canary_size = 8  # Canary bits (2 x 4 bytes)
        # The pak file contains 2 "canary" bits used to detect whether or not the file has been tempered. If they are not set correctly, The game will crash at the loading sequence. 
        # #I'm fairly sure the first one is just the file data offset minus 12, but the 2nd one is interpolated using existing files and associated values - it has quite a large leeway anyways.
        name_offset = header_size + metadata_size + canary_size  # Starting point of the name table
        
        metadata = []
        current_offset = 0
        for relative_path, file_path in files:
            with open(file_path, 'rb') as file_data:
                file_size = os.path.getsize(file_path)
                metadata.append((name_offset, file_size, file_data.read()))
                name_offset += len(relative_path)  # No null-terminator this time
        
        # Canary bits
        name_offset_bk = name_offset - 16
        canary_1 = name_offset - 16  # The offset where file data starts

        # Write file metadata
        name_offset = header_size + metadata_size + canary_size # Reset
        
        for index, (relative_path, (name_off, size, _)) in enumerate(zip(files, metadata)):
            name_off_relative = name_off - header_size
            
            f.write(struct.pack(endian + 'I', name_off_relative))
            f.write(struct.pack(endian + 'I', current_offset))
            f.write(struct.pack(endian + 'I', size))
            f.write(struct.pack(endian + 'B', 0))
            
            current_offset += size

        # Write placeholder for canary bits
        f.write(b'\x00' * 8)
        
        # Write file names
        for relative_path, _ in files:
            f.write(relative_path.encode('utf-8'))
        
        # Write file data
        for index, (_, _, data) in enumerate(metadata):
            f.write(data)

        end_of_file_offset = f.tell()
        
        f.seek(header_size + metadata_size - 3)
        f.write(struct.pack(endian + 'I', canary_1))

        # Here's the estimated formula for canary bit 2. The value is off (not precise), but get pass the check regardless.
        canary_2_value = math.floor(0.00022 * len(files) ** 2 + 33.472 * len(files) - 327.6034)

        canary_2 = int(end_of_file_offset - canary_2_value)
        f.write(struct.pack(endian + 'I', canary_2))
        
        f.seek(0)
        f.write(struct.pack(endian + 'I', end_of_file_offset - 4))
        f.write(struct.pack(endian + 'I', name_offset_bk))
        f.write(struct.pack(endian + 'I', name_offset_bk))
        f.write(struct.pack(endian + 'B', 0))

    print(f"\nPacking complete: {output_file}")

# Main script
if __name__ == "__main__":
    input_folder = input("Enter the folder to pack: ").strip()
    output_file = input("Enter the output .pak file path: ").strip()
    
    if not os.path.isdir(input_folder):
        print("Error: The specified folder does not exist.")
    else:
        pack_pak(input_folder, output_file)
