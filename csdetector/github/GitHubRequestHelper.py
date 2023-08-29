import requests
import logging
import git 
from csdetector import Configuration

class GitHubRequestHelper:
    _tokens = []
    
    @staticmethod
    def get_author_id(author: git.Actor):
        id = ""
        if author.email is None:
            id = author.name.lower().strip()
        else:
            id = author.email.lower().strip()
        return id

    @classmethod
    def init_tokens(cls, config: Configuration):
        cls._tokens = config.pat.copy()

    @classmethod
    def request(cls, url):
        tokens = cls._tokens.copy()

        if len(tokens) == 0:
            logging.error("No tokens available for GitHub API requests")
            raise Exception("No tokens available for GitHub API requests")

        for i in range(len(tokens)):
            try:
                headers = {'Authorization': 'token ' + tokens[i]}
                logging.debug("Requesting {} with token {}".format(url, i))
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response
                else:
                    logging.warning("Token {} failed with status code {}".format(tokens[i], response.status_code))
                    cls._tokens.pop(i)
            except Exception as e:
                logging.warning("Token {} failed with exception {}".format(tokens[i], e))
                cls._tokens.pop(i)
