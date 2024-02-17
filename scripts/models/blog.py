import json

class BlogPost:
    def __init__(self):
        self.__filepath = None
        self.__blogContent = None
        self.__config = None

    # Getter and setter for __filepath
    def get_filepath(self):
        return self.__filepath

    def set_filepath(self, filepath):
        self.__filepath = filepath

    # Getter and setter for __blogContent
    def get_blog_content(self):
        return self.__blogContent

    def set_blog_content(self, content):
        self.__blogContent = content

    # Getter and setter for __config
    def get_config(self):
        return self.__config

    def set_config(self, config):
        if isinstance(config, str):
            try:
                config_dict = json.loads(config)
                print(f"config_dict: {config_dict}")
                self.__config = config_dict
            except json.JSONDecodeError:
                print("Invalid JSON format for config. Config not updated.")
        elif isinstance(config, dict):
            self.__config = config
        else:
            print("Invalid format for config. Config not updated.")