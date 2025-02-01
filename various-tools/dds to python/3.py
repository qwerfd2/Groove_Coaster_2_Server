import os
import imageio.v3 as iio

output_dir = os.path.join(os.getcwd(), "output")
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(os.getcwd()):
    file_path = os.path.join(os.getcwd(), filename)
    
    if filename.lower().endswith(".dds") and os.path.isfile(file_path):
        try:
            img = iio.imread(file_path)
            new_filename = os.path.splitext(filename)[0] + ".png"
            new_file_path = os.path.join(output_dir, new_filename)
            iio.imwrite(new_file_path, img, extension=".png")
            print(f"Converted: {filename} -> {new_filename}")
        except Exception as e:
            print(f"Error converting {filename}: {e}")
