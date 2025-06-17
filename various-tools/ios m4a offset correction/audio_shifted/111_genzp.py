import os

SEVEN_ZIP_PATH = r"C:\Program Files\7-Zip\7z.exe"

PASSWORD = "eiprblFFv69R83J5"

OUTPUT_FOLDER = "output"

def generate_zipcrypto_commands():
    cwd = os.getcwd()
    output_path = os.path.join(cwd, OUTPUT_FOLDER)

    os.makedirs(output_path, exist_ok=True)

    commands = []

    for root, _, files in os.walk(cwd):
        if root == output_path:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            zip_filename = file + ".zip"
            zip_path = os.path.join(output_path, zip_filename)

            cmd = f'"{SEVEN_ZIP_PATH}" a -p{PASSWORD} -mem=ZipCrypto "{zip_path}" "{file_path}"'
            commands.append(cmd)

    return commands

if __name__ == "__main__":
    zip_commands = generate_zipcrypto_commands()
    
    for cmd in zip_commands:
        print(cmd)