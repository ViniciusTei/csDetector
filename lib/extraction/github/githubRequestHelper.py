import requests

class GithubRequestHelper:
    _token = None

    def setToken(self, pat: str):
        self._token = pat
    
    def requests(self, initalUrl) -> list[requests.Response] | None:
        allResponses = []

        try:
            url = initalUrl
            while (url):
                headers = {'Authroization': f'bearer {self._token}'}
                response = requests.get(url, headers=headers)
                print(f'From: {url} \n Response: <{response.status_code}> ')

                if response.status_code == 200:
                    allResponses.append(response)

                if response.links and response.links['next']:
                    url = response.links['next']['url']
                else:
                    url = None

        except:
            self._token = None

        return allResponses


