import logging
import os
from dateutil.relativedelta import relativedelta
import sentistrength
from git.repo import Repo

from csdetector import Configuration, utils
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper
from csdetector.metrics.authorAlias import AuthorAlias
from csdetector.metrics.centralityAnalysis import CentralityAnalysis
from csdetector.metrics.commitAnalysis import CommitAnalysis
from csdetector.metrics.pullRequestAnalysis import PRAnalysis
from csdetector.metrics.releaseAnalysis import ReleaseAnalysis
from csdetector.metrics.tagAnalysis import TagAnalysis

class CommunitySmells:
    _config: Configuration
    _repo: Repo
    _senti: sentistrength.PySentiStr
    _request: GitHubRequestController

    def __init__(self, config: Configuration):
        self._config = config
        
        # prepare folders
        if os.path.exists(self._config.resultsPath):
            utils.remove_tree(self._config.resultsPath)

        os.makedirs(self._config.metricsPath)

        # get repository reference
        self._repo = utils.getRepo(self._config)
        
        # setup sentiment analysis
        self._senti = sentistrength.PySentiStr()

        sentiJarPath = os.path.join(
            config.sentiStrengthPath, "SentiStrength.jar").replace("\\", "/")
        self._senti.setSentiStrengthPath(sentiJarPath)

        sentiDataPath = os.path.join(
            config.sentiStrengthPath, "SentiStrength_Data").replace("\\", "/") + "/"
        self._senti.setSentiStrengthLanguageFolderPath(sentiDataPath)
        
        self._request = GitHubRequestController(self._config)
        
        logging.info("CSFactory initialized")

    def detect(self):
        # A - mine developer aliases
        authorAliasExtractor = AuthorAlias(self._config, self._repo, self._request)
        authorAliasExtractor.extract()

        # B - build social network graphs
        delta = relativedelta(months=+self._config.batchMonths)
        commits = list(authorAliasExtractor.replaceAliases())

        commitAnalysis = CommitAnalysis(self._senti, commits, delta, self._config)
        batchDates, authorInfoDict, daysActive = commitAnalysis.extract()


        TagAnalysis(self._config, self._repo, delta, batchDates, daysActive).extract()
        cA = CentralityAnalysis(self._config, commits, delta, batchDates)

        coreDevs = cA.extract()

        ReleaseAnalysis(self._config).extract(commits, delta, batchDates)
        
        prA = PRAnalysis(self._config) 
        prParticipantBatches, prCommentBatches = prA.extract(self._senti, delta, batchDates, cA)
        logging.info("PR Analysis completed")
        logging.info("PR Participant Batches: %s", prParticipantBatches)
        logging.info("PR Comment Batches: %s", prCommentBatches)

        # C - Compute Sentiment metrics
        # D - Compute Social metrics
        # E - Smell Detection with pre-trained models
        
        return ['a', 'b', 'c']
