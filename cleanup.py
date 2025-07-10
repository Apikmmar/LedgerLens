import os
import shutil

def delete_pycache_and_pyc(start_path='.'):
    deleted = 0
    for root, dirs, files in os.walk(start_path):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)
                print(f"Deleted folder: {dir_path}")
                deleted += 1
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
                deleted += 1

    if deleted == 0:
        print("No __pycache__ or .pyc files found.")
    else:
        print(f"✅ Deleted {deleted} items.")

if __name__ == "__main__":
    delete_pycache_and_pyc()
