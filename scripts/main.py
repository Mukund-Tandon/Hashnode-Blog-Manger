import sys
import json
def process_content():
    s = ""
    for line in sys.stdin:
        s = s + line + "\n"

    data = json.loads(s)
    print(data)
        

if __name__ == "__main__":
    process_content()