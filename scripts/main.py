import sys
import os

def open_files(file_paths):
    for file_path in file_paths:
        print(f"Opening file: {file_path}")
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                print(f"File content:\n{repr(content)}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

if __name__ == "__main__":
    # Read file paths from standard input
    file_paths = sys.stdin.read().strip().split('\n')

    # Check if any file paths were received
    if not file_paths:
        print("No files to process.")
    else:
        open_files(file_paths)
