import logging
import re
from strsimpy.metric_lcs import MetricLCS

from csdetector import Configuration
from csdetector.github.GitHubResquestCommits import GitHubRequestCommits
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper 
from csdetector.utils import getRepo

# TODO: add output to file
# TODO: filter out emails that belong to bot accounts
class AuthorAlias:
    _request: GitHubRequestHelper
    _aliases: dict

    def __init__(self, config: Configuration):
        self._config = config
        self._request = GitHubRequestHelper()
        self._request.init_tokens(self._config)
        self._repo = getRepo(self._config)

    # apply Levenshtein distance to the local part of the email
    def _areSimilar(self, valueA: str, valueB: str, maxDistance: float):
        lcs = MetricLCS()
        expr = r"(.+)@"

        localPartAMatches = re.findall(expr, valueA)
        localPartBMatches = re.findall(expr, valueB)

        if len(localPartAMatches) == 0:
            localPartAMatches = [valueA]

        if len(localPartBMatches) == 0:
            localPartBMatches = [valueB]

        distance = lcs.distance(localPartAMatches[0], localPartBMatches[0])

        return distance <= maxDistance

    def extract(self):
        commits = list(self._repo.iter_commits())

        emails = []

        for commit in commits:
            emails.append(GitHubRequestHelper.get_author_id(commit.author))

        logging.info("Extracting author aliases from {} commits and {} emails".format(len(commits), len(emails)))
        commitshaByEmail = self._exctrachCommitsByEmails(emails)

        (loginByEmail, emailsWithoutLogins) = self._requestGithubAndRetrieveLogins(commitshaByEmail)
            
        aliases = {}
        usedAsValues = {}

        for email in loginByEmail:
            login = loginByEmail[email]
            aliasEmail = aliases.setdefault(login, [])
            aliasEmail.append(email)
            usedAsValues[email] = login

        if len(emailsWithoutLogins) > 0:
            for authorA in emailsWithoutLogins:
                quickMatched = False
                
                for key in usedAsValues:
                    if authorA == key:
                        quickMatched = True
                        continue

                    if self._areSimilar(authorA, key, self._config.maxDistance):
                        alias = usedAsValues[key]
                        aliases[alias].append(authorA)
                        usedAsValues[authorA] = alias
                        quickMatched = True
                        break

                if quickMatched:
                    continue

                for key in aliases:
                    if authorA == key:
                        quickMatched = True
                        continue

                    if self._areSimilar(authorA, key, self._config.maxDistance):
                        aliases[key].append(authorA)
                        usedAsValues[authorA] = key
                        quickMatched = True
                        break

                if quickMatched:
                    continue

                for authorB in emailsWithoutLogins:
                    if authorA == authorB:
                        continue

                    if self._areSimilar(authorA, authorB, self._config.maxDistance):
                        aliasedAuthor = aliases.setdefault(authorA, [])
                        aliasedAuthor.append(authorB)
                        usedAsValues[authorB] = authorA
                        break

        self._aliases = aliases
        # returm dictionary of aliases
        # key: alias
        # value: list of emails
        return aliases

    def replaceAliases(self):
        if self._aliases is None:
            raise Exception("Aliases are not extracted yet, run extract() first")

        commits = list(self._repo.iter_commits())
        
        aliases = self._aliases
        # transpose for easy replacements
        transposesAliases = {}
        for alias in aliases:
            for email in aliases[alias]:
                transposesAliases[email] = alias

        # replace all author aliases with a unique one
        return self._replaceAll(commits, transposesAliases)


    def _replaceAll(self, commits, aliases):
        for commit in commits:
            copy = commit
            author = GitHubRequestHelper.get_author_id(commit.author)

            if author in aliases:
                copy.author.email = aliases[author]

            yield copy

    def _requestGithubAndRetrieveLogins(self, commitshaByEmail):
        loginByEmail = {}
        emailsWithoutLogins = []

        for commit in commitshaByEmail:
            sha = commitshaByEmail[commit]
            commitUrl = GitHubRequestCommits.requestUrl(self._config, sha)
            response = self._request.request(commitUrl)

            if response is None:
                continue

            commit = response.json()

            email = commit['commit']['author']['email']

            if commit['author'] is None:
                emailsWithoutLogins.append(email)
                continue

            if commit['author']['login'] is not None:
                loginByEmail[email] = commit['author']['login']
            else:
                emailsWithoutLogins.append(email)
            
        return (loginByEmail, emailsWithoutLogins)

    def _exctrachCommitsByEmails(self, emails):
        commitshaByEmail = {}

        for email in emails:
            commit = next(
                commit
                for commit in self._repo.iter_commits()
                if GitHubRequestHelper.get_author_id(commit.author) == email
            )

            commitshaByEmail[email] = commit.hexsha

        return commitshaByEmail

