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


def checkBlogStatus(blog,blog_ids):
#     script_dir = os.path.dirname(os.path.realpath(__file__))

# # Construct the absolute path to the JSON file
#     blog_ids_file = os.path.join(script_dir, '..', 'blog_ids.json')
    blog_status = BlogStatus()
    with open('blog_ids.json', 'r') as file:
        blog_ids_json = json.load(file)
        print(f"Blog IDs JSON: {blog_ids_json}")
    list_of_blog_ids = blog_ids_json['ids']
    print(f"List of blog IDs: {list_of_blog_ids}")
    filepath = blog.get_filepath()
    print(f"Filepath: {filepath}")
    if filepath in list_of_blog_ids:
        blog_status.id = list_of_blog_ids[filepath]
        blog_status.isNew = False
    else:
        blog_status.isNew = True

    
    # Check if blog has a filepath



    return blog_status


def main():
    public_key = os.environ.get('PUBLIC_KEY')
    hashnode_api_token = os.environ.get('HASHNODE_ACCESS_TOKEN')
    publication_id = os.environ.get('PUBLICATION_ID')
    github_api_token = os.environ.get('GITHUB_API_TOKEN')
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    blog_ids = os.environ.get('BLOG_IDS')
    # Read file paths from standard input
    file_paths = sys.stdin.read().strip().split('\n')

    # Check if any file paths were received
    if not file_paths:
        print("No files to process.")
        #TODO: how to throw errors which fail the github action?
        return
    
    blog = getBlogFromFilePath(file_paths)
    print("Blog object created")
    blog_status = checkBlogStatus(blog,blog_ids)
    print("Blog status checked")




if __name__ == "__main__":
    main()
