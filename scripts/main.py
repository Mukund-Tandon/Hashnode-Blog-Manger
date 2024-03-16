import sys
import os
import json
import requests
from models.blog import BlogPost
from models.blogStatus import BlogStatus
graphql_endpoint = "https://gql.hashnode.com"
def process_yaml():
    try:
        with open('config.json', 'r') as file:
            config_data = json.load(file)
            return config_data
    except FileNotFoundError:
        print("config.json file not found")
        exit(1)


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


def create_blog_post(blog,hashnode_api_token,github_api_token,publication_id):
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
