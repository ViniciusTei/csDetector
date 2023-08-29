import logging
import yaml
import os
import re
from git.repo import Repo
from strsimpy.metric_lcs import MetricLCS

from csdetector import Configuration
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.github.GitHubResquestCommits import GitHubRequestCommits
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper 

# TODO: add output to file
# TODO: filter out emails that belong to bot accounts
class AuthorAlias:
    _request: GitHubRequestController
    _aliases: dict

    def __init__(self, config: Configuration, repo: Repo, request: GitHubRequestController) -> None:
        self._config = config
        self._repo = repo
        self._request = request
        self._request.setStrategy(strategy=GitHubRequestCommits)
        self._aliases = dict()

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

        aliasPath = os.path.join(self._config.repositoryPath, "aliases.yml")
        logging.info("Writing aliases to '{0}'".format(aliasPath))
        if not os.path.exists(os.path.dirname(aliasPath)):
            os.makedirs(os.path.dirname(aliasPath))

        with open(aliasPath, "a", newline="") as f:
            yaml.dump(aliases, f)

        logging.info("Extracted {} aliases".format(len(aliases)))
        return aliases

    def replaceAliases(self):
        commits = list(self._repo.iter_commits())
        
        if self._aliases is None:
            return commits

        try:
            aliases = self._aliases
            # transpose for easy replacements
            transposesAliases = {}
            logging.info("Replacing aliases")
            for alias in aliases:
                for email in aliases[alias]:
                    transposesAliases[email] = alias

            # replace all author aliases with a unique one
            return self._replaceAll(commits, transposesAliases)

        except NameError as e:
            return commits

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
            #TODO: refactor this crapy code, sorry... I just want to finish this
            commitUrl = GitHubRequestCommits.urlCommitBySha(self._config, sha)
            response = self._request.request.request(commitUrl)

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

