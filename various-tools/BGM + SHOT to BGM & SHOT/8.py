import numpy as np
import scipy.io.wavfile as wav
import os
import sys

if len(sys.argv) != 4:
    print("Usage: 8.py <bgm_wav> <shot_wav> <shot_wav>")
    sys.exit(1)

file1 = sys.argv[1]
file2 = sys.argv[2]

rate1, data1 = wav.read(file1)
rate2, data2 = wav.read(file2)

if rate1 != rate2:
    raise ValueError("Sample rate mismatch!")

if data1.ndim != data2.ndim:
    raise ValueError("Channel count mismatch!")

# Find the minimum length of the two arrays
min_length = min(len(data1), len(data2))

# Trim both arrays to the same length
data1 = data1[:min_length]
data2 = data2[:min_length]

# Convert to int32, perform addition (without normalization), and clip values
data1 = data1.astype(np.int32)
data2 = data2.astype(np.int32)

mixed = data1 + data2
mixed = np.clip(mixed, -32768, 32767).astype(np.int16)

dir_name, base_name = os.path.split(file2)
output_file = file2  # Overwrite the shot file with the mixed output

wav.write(output_file, rate1, mixed)

print(f"Mixing complete! Saved as {output_file}")
