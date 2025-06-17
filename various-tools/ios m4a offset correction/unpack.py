import os
import zipfile
import threading
import traceback

ZIP_PASSWORD = b"eiprblFFv69R83J5"
OUTPUT_DIR = "audio"
MAX_THREADS = 4
semaphore = threading.Semaphore(MAX_THREADS)

def unpack_zip(zip_path):
    with semaphore:
        try:
            with zipfile.ZipFile(zip_path) as zf:
                print(f"Extracting {zip_path}...")
                zf.extractall(OUTPUT_DIR, pwd=ZIP_PASSWORD)
            print(f"Unpacked: {zip_path}")
        except Exception as e:
            print(f"Failed to unpack {zip_path}: {e}")
            traceback.print_exc()

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    zip_files = [f for f in os.listdir('.') if f.lower().endswith('.zip')]
    print(f"Found ZIP files: {zip_files}")
    threads = []

    for zip_file in zip_files:
        t = threading.Thread(target=unpack_zip, args=(zip_file,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()