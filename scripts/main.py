import sys
import os
import json
import requests
from models.blog import BlogPost
from models.blogStatus import BlogStatus
from base64 import b64encode

from nacl import encoding, public
graphql_endpoint = "https://gql.hashnode.com"
def process_yaml():
    try:
        with open('config.json', 'r') as file:
            config_data = json.load(file)
            return config_data
    except FileNotFoundError:
        print("config.json file not found")
        exit(1)

def encrypt(public_key: str, secret_value: str) -> str:
  """Encrypt a Unicode string using the public key."""
  public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
  sealed_box = public.SealedBox(public_key)
  encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
  return b64encode(encrypted).decode("utf-8")

def getBlogFromFilePath(file_paths):
    if len(file_paths) > 2:
        raise ValueError("Exactly two file paths are required")

    blog = BlogPost()

    for file_path in file_paths:
        print(f"Opening file: {file_path}")
        try:
            with open(file_path, 'r') as file:
                content = file.read()

                if file_path.endswith(".md"):
                    blog.set_filepath(file_path)
                    blog.set_blog_content(content)
                elif file_path.endswith(".json"):
                    blog.set_config(json.loads(content))
                else:
                    print(f"Ignoring file with unknown extension: {file_path}")

                print(f"File content:\n{content}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    print("Done creting blog object now going back to main function")
    return blog


def checkBlogStatus(blog):
#     script_dir = os.path.dirname(os.path.realpath(__file__))

# # Construct the absolute path to the JSON file
#     blog_ids_file = os.path.join(script_dir, '..', 'blog_ids.json')
    blog_status = BlogStatus()
    file_contents = {}
    with open('../action-repo/scripts/blog_ids.txt', 'r') as file:
        for line in file:
        # Split the line based on the delimiter ":-"
            parts = line.strip().split(":-")
            # Check if the line has the expected format
            if len(parts) == 2:
                key = parts[0].strip()  # Extract the key
                value = parts[1].strip()  # Extract the value
                # Store the key-value pair in the dictionary
                file_contents[key] = value

    print(f"File contents: {file_contents}")
    print(f"Filepath: {blog.get_filepath()}")

    if blog.get_filepath() in file_contents:
        blog_status.id = file_contents[blog.get_filepath()]
        blog_status.isNew = False
    else:
        blog_status.isNew = True
    
    print(f"Blog status: {blog_status}")
    return blog_status
    



    return blog_status


def append_to_blog_ids(data_to_append):
    with open("../action-repo/scripts/blog_ids.txt", "r") as file:
        existing_data = file.read()

    updated_data = existing_data.strip()  # Remove trailing newline if present
    if updated_data:  # Add a newline only if the file is not empty
        updated_data += "\n"
    updated_data += data_to_append

    return updated_data

def get_public_key_from_github(github_api_token,github_repository):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_api_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/repos/{github_repository}/actions/secrets/public-key"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['key_id'], data['key']
    else:
        print(f"Failed to retrieve public key: {response.status_code}")
        return None, None


def update_secret_on_github(github_api_token, github_repository, secret_name, encrypted_value, key_id):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_api_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    url = f"https://api.github.com/repos/{github_repository}/actions/secrets/{secret_name}"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 204:
        print(f"Secret '{secret_name}' updated successfully.")
    else:
        print(f"Failed to update secret '{secret_name}': {response.status_code}")

    

def create_blog_post(blog,hashnode_api_token,github_api_token,publication_id,github_repository):
    config_data = blog.get_config()
    config_data['contentMarkdown'] = blog.get_blog_content()
    config_data['publicationId'] = publication_id

    headers = {
    "Authorization": hashnode_api_token
    }
    mutation_input = {
    "input": config_data
    }
    mutation_query = """
        mutation PublishPost($input: PublishPostInput!) {
            publishPost(input: $input) {
                post {
                id
                }
            }
        }
    """
    
    response = requests.post(graphql_endpoint, json={"query": mutation_query, "variables": mutation_input}, headers=headers)
    response_data = response.json()
    print(f"Response: {response_data}")
    if "errors" in response_data:
        print(f"Error: {response_data['errors']}")
        return
    post_id = response_data['data']['publishPost']['post']['id']
    blog_path = blog.get_filepath()
    blog_path_id_pair_to_store = f"{blog_path}:-{post_id}"
    key_id, public_key = get_public_key_from_github(github_api_token, github_repository)
    print(f"Public key: {public_key}")
    updated_data = append_to_blog_ids(blog_path_id_pair_to_store)
    encryptes_value = encrypt(public_key, updated_data)
    print(f"Encrypted value: {encryptes_value}")

def main():
    public_key = os.environ.get('PUBLIC_KEY')
    hashnode_api_token = os.environ.get('HASHNODE_ACCESS_TOKEN')
    publication_id = os.environ.get('PUBLICATION_ID')
    github_api_token = os.environ.get('GITHUB_API_TOKEN')
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    # blog_ids = os.environ.get('BLOG_IDS')
    # Read file paths from standard input
    file_paths = sys.stdin.read().strip().split('\n')

    # Check if any file paths were received
    if not file_paths:
        print("No files to process.")
        #TODO: how to throw errors which fail the github action?
        return

    blog = getBlogFromFilePath(file_paths)
    print("Blog object created")
    blog_status = checkBlogStatus(blog)
    print("Blog status checked")

    if blog_status.isNew:
        create_blog_post(blog,hashnode_api_token,github_api_token,publication_id)






if __name__ == "__main__":
    main()
