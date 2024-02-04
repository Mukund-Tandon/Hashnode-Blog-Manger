import sys
import json
def process_content():
    json_str = sys.argv[1]
    data = json.loads(json_str)

    print(data) 

if __name__ == "__main__":
    process_content()