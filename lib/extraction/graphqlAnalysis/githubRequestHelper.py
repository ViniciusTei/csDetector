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
        except Exception as e:
            self._token = None

    def numeroTotalPaginas(self, url):
        response = self.requests(url=url)
        if response.links.keys():
            return int(response.link['last']['url'].partition('&page=')[-1])
        else:
            return 1
