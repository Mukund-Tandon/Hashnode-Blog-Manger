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
  public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
  sealed_box = public.SealedBox(public_key)
  encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
  return b64encode(encrypted).decode("utf-8")

def getBlogFromFilePath(file_paths):
    if len(file_paths) > 2:
        raise ValueError("Exactly two file paths are required")

    blog = BlogPost()

    for file_path in file_paths:
        try:
            with open(file_path, 'r') as file:
                content = file.read()

                if file_path.endswith(".md"):
                    directory_path = os.path.dirname(file_path)
                    if(blog.get_filepath() != None and blog.get_filepath() != directory_path):
                        print("Both blog md and config files should be in same directory")
                        exit(1)
                        
                    blog.set_filepath(directory_path)
                    blog.set_blog_content(content)
                elif file_path.endswith(".json"):
                    directory_path = os.path.dirname(file_path)
                    if(blog.get_filepath() != None and blog.get_filepath() != directory_path):
                        print("Both blog md and config files should be in same directory")
                        exit(1)
                    blog.set_filepath(directory_path)
                    blog.set_config(json.loads(content))
                else:
                    print(f"Ignoring file with unknown extension: {file_path}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    return blog

def checkBlogStatus(blog):
    blog_status = BlogStatus()
    file_contents = {}
    with open('../action-repo/scripts/blog_ids.txt', 'r') as file:
        for line in file:
            parts = line.strip().split(":-")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                file_contents[key] = value

    if blog.get_filepath() in file_contents:
        blog_status.id = file_contents[blog.get_filepath()]
        blog_status.isNew = False
    else:
        if blog.get_config() is None or blog.get_blog_content() is None:
            print("Both config and md files are required to create a new blog post")
            exit(1)
        blog_status.isNew = True
    
    return blog_status

def append_to_blog_ids(data_to_append):
    with open("../action-repo/scripts/blog_ids.txt", "r") as file:
        existing_data = file.read()

    updated_data = existing_data.strip()
    if updated_data:
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
    if "errors" in response_data:
        print(f"Error: {response_data['errors']}")
        exit(1)
        return
    post_id = response_data['data']['publishPost']['post']['id']
    blog_path = blog.get_filepath()
    blog_path_id_pair_to_store = f"{blog_path}:-{post_id}"
    key_id, public_key = get_public_key_from_github(github_api_token, github_repository)
    updated_data = append_to_blog_ids(blog_path_id_pair_to_store)
    encryptes_value = encrypt(public_key, updated_data)
    update_secret_on_github(github_api_token, github_repository, "BLOG_IDS", encryptes_value, key_id)
    print(f"Blog published ")

def update_blog_post(blog,hashnode_api_token,blog_id):
    config_data = blog.get_config()
    if config_data != None:
        if blog.get_blog_content() != None:
            config_data['contentMarkdown'] = blog.get_blog_content()
    else:
        config_data = {
            "contentMarkdown": blog.get_blog_content()
        }
    
    config_data['id'] = blog_id
    headers = {
    "Authorization": hashnode_api_token
    }
    mutation_input = {
    "input": config_data
    }
    mutation_query = """
        mutation UpdatePost($input: UpdatePostInput!) {
            updatePost(input: $input) {
                post {
                id
                }
            }
        }
    """

    response = requests.post(graphql_endpoint, json={"query": mutation_query, "variables": mutation_input}, headers=headers)
    response_data = response.json()
    if "errors" in response_data:
        print(f"Error: {response_data['errors']}")
        exit(1)
        return
    post_id = response_data['data']['updatePost']['post']['id']
    print(f"Blog updated ")

def main():
    public_key = os.environ.get('PUBLIC_KEY')
    hashnode_api_token = os.environ.get('HASHNODE_ACCESS_TOKEN')
    publication_id = os.environ.get('PUBLICATION_ID')
    github_api_token = os.environ.get('GITHUB_API_TOKEN')
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    file_paths = sys.stdin.read().strip().split('\n')

    if not file_paths:
        print("No files to process.")
        return

    blog = getBlogFromFilePath(file_paths)
    blog_status = checkBlogStatus(blog)

    if blog_status.isNew:
        create_blog_post(blog,hashnode_api_token,github_api_token,publication_id,github_repository)
    else:
        print(f"Blog already published")
        update_blog_post(blog,hashnode_api_token,blog_status.id)

if __name__ == "__main__":
    main()