import sys

def process_content():
    for line in sys.stdin:
        # Process each line of input as needed
        print(line.strip())  # Example: Print the stripped content of each line

if __name__ == "__main__":
    process_content()