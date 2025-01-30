import numpy as np
import scipy.io.wavfile as wav
import os

file1 = input("Enter the first WAV file (music track): ").strip()
file2 = input("Enter the second WAV file (SFX track): ").strip()

rate1, data1 = wav.read(file1)
rate2, data2 = wav.read(file2)

if rate1 != rate2:
    raise ValueError("Sample rate mismatch!")

if data1.ndim != data2.ndim:
    raise ValueError("Channel count mismatch!")

# Convert to int32, addition (not normalization), then cap values.
data1 = data1.astype(np.int32)
data2 = data2.astype(np.int32)

mixed = data1 + data2

mixed = np.clip(mixed, -32768, 32767)

mixed = mixed.astype(np.int16)

dir_name, base_name = os.path.split(file2)
output_file = os.path.join(dir_name, "1_" + base_name)

wav.write(output_file, rate1, mixed)

print(f"Mixing complete! Saved as {output_file}")