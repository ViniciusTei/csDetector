import requests

class GithubRequestHelper:
    _token = None
    _request = None

    def setToken(self, pat):
        self._token = pat
    
    def requests(self, url):
        try:
            headers = {'Authroization': 'bearer ' + self._token}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response
            else:
                self._token = None
        except:
            self._token = None

    def getRequestsTotalPages(self, url):
        try:
            response = self.requests(url=url)
            if response.links.keys():
                return int(response.link['last']['url'].partition('&page=')[-1])
            else:
                return 1
        except Exception as e:
            raise Exception(f"Query execution failed {e}")


class PullRequestsExctractor(GithubRequestHelper):
    def __init__(self) -> None:
        super().__init__()
    def requestPR(self):
        totalPages = self.getRequestsTotalPages('pullRequests')
        response = self.requests('pullRequests')
