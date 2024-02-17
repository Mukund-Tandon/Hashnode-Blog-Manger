import sys
import os
import json
import requests
from models.blog import BlogPost
from models.blogStatus import BlogStatus




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


def checkBlogStatus(blog,github_api_token,github_repository):
    blog_staus = BlogStatus()
    url = f"https://api.github.com/repos/{github_repository}/actions/secrets/BLOG_IDS"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_api_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    print("1")
    try:
        response = requests.get(url, headers=headers)
        print("2")
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        print("2")
        secret_data = response.json()
        print("2")
        print("Secret data below ------>")
        print(secret_data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching secret from GitHub API: {e}")
        return None


    return blog_status


def main():
    public_key = os.environ.get('PUBLIC_KEY')
    hashnode_api_token = os.environ.get('HASHNODE_ACCESS_TOKEN')
    publication_id = os.environ.get('PUBLICATION_ID')
    github_api_token = os.environ.get('GITHUB_API_TOKEN')
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    # Read file paths from standard input
    file_paths = sys.stdin.read().strip().split('\n')

    # Check if any file paths were received
    if not file_paths:
        print("No files to process.")
        #TODO: how to throw errors which fail the github action?
        return
    
    blog = getBlogFromFilePath(file_paths)
    print("Blog object created")
    blog_status = checkBlogStatus(blog,github_api_token,github_repository)
    print("Blog status checked")




if __name__ == "__main__":
    main()
