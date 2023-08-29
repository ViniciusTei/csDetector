import logging
import os
from dateutil.relativedelta import relativedelta
import sentistrength
from git.repo import Repo

from csdetector import Configuration, utils
from csdetector.detection.SmellDetection import SmellDetection
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.metrics.authorAlias import AuthorAlias
from csdetector.metrics.centralityAnalysis import CentralityAnalysis
from csdetector.metrics.commitAnalysis import CommitAnalysis
from csdetector.metrics.devAnalysis import DevAnalysis
from csdetector.metrics.issueAnalysis import IssueAnalysis
from csdetector.metrics.politnessAnalysis import PolitnessAnalysis
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

        if (self._config.aliasExtract):
            authorAliasExtractor.extract()

        # B - build social network graphs
        delta = relativedelta(months=+self._config.batchMonths)
        commits = list(authorAliasExtractor.replaceAliases())

        commitAnalysis = CommitAnalysis(self._senti, commits, delta, self._config)
        batchDates, authorInfoDict, daysActive = commitAnalysis.extract()


        TagAnalysis(self._config, self._repo, delta, batchDates, daysActive).extract()
        cA = CentralityAnalysis(self._config, commits, delta, batchDates)

        coreDevs = cA.extract()

        ReleaseAnalysis(self._config, self._request).extract(commits, delta, batchDates)
        
        prA = PRAnalysis(self._config, self._request) 
        prParticipantBatches, prCommentBatches = prA.extract(self._senti, delta, batchDates, cA)
        logging.info("PR Analysis completed")

        issueA = IssueAnalysis(self._config, self._request)
        issueParticipantBatches, issueCommentBatches = issueA.extract(self._senti, delta, batchDates, cA)
        logging.info("Issue Analysis completed")

        # C - Compute Sentiment metrics
        PolitnessAnalysis.calculateACCL(self._config, prCommentBatches, issueCommentBatches)
        PolitnessAnalysis.calculateRPC(self._config, "PR", prCommentBatches)
        PolitnessAnalysis.calculateRPC(self._config, "Issue", issueCommentBatches)

        # D - Compute Social metrics
        results = []
        for batchIdx, batchDate in enumerate(batchDates):

            # get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batchIdx] +
                issueParticipantBatches[batchIdx]
            )

            # build combined network
            cA.buildGraph(
                batchIdx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
            )

            # get combined unique authors for both PRs and issues
            uniqueAuthorsInPrBatch = set(
                author for pr in prParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInIssueBatch = set(
                author for pr in issueParticipantBatches[batchIdx] for author in pr
            )

            uniqueAuthorsInBatch = uniqueAuthorsInPrBatch.union(
                uniqueAuthorsInIssueBatch
            )

            # get batch core team
            batchCoreDevs = coreDevs[batchIdx]

            # run dev analysis
            DevAnalysis.analyse(
                authorInfoDict,
                batchIdx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                self._config,
            )
            
            # E - Smell Detection with pre-trained models
            results.append(self.__detectSmells(batchIdx, batchDate))

        detectedSmells, detectedSmellsDict = results[0]

        return detectedSmells, detectedSmellsDict

    def __detectSmells(self, batchIdx, batchDate):
        logging.info("Detecting smells for batch " + str(batchIdx))
        detectedSmells = None
        result = {}
        # run smell detection
        detectedSmells = SmellDetection.smellDetection(self._config, batchIdx)

        # building a dictionary of detected community smells for each batch analyzed
        result["Index"] = batchIdx
        result["StartingDate"] = batchDate.strftime("%m/%d/%Y")

        # separating smells and converting in their full name
        for index, smell in enumerate(detectedSmells):
            if(index != 0):
                smellName = "Smell" + str(index)
                result[smellName] = [
                    smell, SmellDetection.get_community_smell_name(detectedSmells[index])]
        
        SmellDetection.add_to_smells_dataset(
            self._config, batchDate.strftime("%m/%d/%Y"), detectedSmells
        )
    
        return detectedSmells, result
