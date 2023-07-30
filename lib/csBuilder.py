import sys
import os
import pkg_resources
import sentistrength
import pandas as pd
import lib.extraction.centralityAnalysis as centrality
from dateutil.relativedelta import relativedelta
from lib.devAnalysis import devAnalysis
from lib.configuration import parseDevNetworkArgs
from lib.extraction.repoLoader import getRepo
from lib.extraction.aliasWorker import replaceAliases
from lib.extraction.authorAliasExtractor import authorAliasExtractor
from lib.extraction.commitAnalysis import commitAnalysis
from lib.extraction.tagAnalysis import tagAnalysis
from lib.extraction.graphqlAnalysis.releaseAnalysis import releaseAnalysis
from lib.extraction.graphqlAnalysis.prAnalysis import prAnalysis
from lib.extraction.graphqlAnalysis.issueAnalysis import issueAnalysis
from lib.extraction.politenessAnalysis import politenessAnalysis
from lib.detection.smellDetection import smellDetection
from lib.utils import remove_tree

class CSBuilder():
    def __init__(self, argv) -> None:
        # validate running in venv
        if not hasattr(sys, "prefix"):
            raise Exception(
                "The tool does not appear to be running in the virtual environment!\nSee README for activation."
            )

        # validate python version
        if sys.version_info.major != 3 or sys.version_info.minor > 10:
            raise Exception(
                "Expected Python less then 3.10 as runtime but got {0}.{1}, the tool might not run as expected!\nSee README for stack requirements.".format(
                    sys.version_info.major,
                    sys.version_info.minor,
                    sys.version_info.micro,
                )
            )

        # validate installed modules
        required = {
            "wheel",
            "networkx",
            "pandas",
            "matplotlib",
            "gitpython",
            "requests",
            "pyyaml",
            "progress",
            "strsimpy",
            "python-dateutil",
            "sentistrength",
            "joblib",
        }
        installed = {pkg for pkg in pkg_resources.working_set.by_key}
        missing = required - installed

        if len(missing) > 0:
            raise Exception(
                "Missing required modules: {0}.\nSee README for tool installation.".format(
                    missing
                )
            )

        # parse args
        self.__config = parseDevNetworkArgs(argv)
        # prepare folders
        if os.path.exists(self.__config.resultsPath):
            remove_tree(self.__config.resultsPath)

        os.makedirs(self.__config.metricsPath)

        # get repository reference
        self.__repo = getRepo(self.__config)

        # setup sentiment analysis
        self.__senti = sentistrength.PySentiStr()

        sentiJarPath = os.path.join(
            self.__config.sentiStrengthPath, "SentiStrength.jar").replace("\\", "/")
        self.__senti.setSentiStrengthPath(sentiJarPath)

        sentiDataPath = os.path.join(
            self.__config.sentiStrengthPath, "SentiStrength_Data").replace("\\", "/") + "/"
        self.__senti.setSentiStrengthLanguageFolderPath(sentiDataPath)

        # prepare batch delta
        self.__delta = relativedelta(months=+self.__config.batchMonths)

        pass

    def __mineDevelopersAliases(self):
        # exctract aliases
        authorAliasExtractor(self.__config.repositoryUrl, self.__config.outputPath, 0.75, self.__config.pat, self.__config.startDate)
        # handle aliases
        commits = list(replaceAliases(self.__repo.iter_commits(), self.__config))
        return commits

    def __buildSocialNetworkGraphs(self, commits):
        # run analysis
        batchDates, authorInfoDict, daysActive = commitAnalysis(
            self.__senti, commits, self.__delta, self.__config
        )

        tagAnalysis(self.__repo, self.__delta, batchDates, daysActive, self.__config)

        coreDevs = centrality.centralityAnalysis(
            commits, self.__delta, batchDates, self.__config)

        releaseAnalysis(commits, self.__config, self.__delta, batchDates)

        prParticipantBatches, prCommentBatches = prAnalysis(
            self.__config,
            self.__senti,
            self.__delta,
            batchDates,
        )

        issueParticipantBatches, issueCommentBatches = issueAnalysis(
            self.__config,
            self.__senti,
            self.__delta,
            batchDates,
        )
        
        politenessAnalysis(self.__config, prCommentBatches, issueCommentBatches)
        return authorInfoDict, batchDates, coreDevs, prParticipantBatches, issueParticipantBatches
    
    def __computSentimentsMetrics(self, authorInfoDict, batchDates, prParticipantBatches, issueParticipantBatches, coreDevs):
        results = []
        for batchIdx, batchDate in enumerate(batchDates):

            # get combined author lists
            combinedAuthorsInBatch = (
                prParticipantBatches[batchIdx] +
                issueParticipantBatches[batchIdx]
            )

            # build combined network
            centrality.buildGraphQlNetwork(
                batchIdx,
                combinedAuthorsInBatch,
                "issuesAndPRsCentrality",
                self.__config,
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
            devAnalysis(
                authorInfoDict,
                batchIdx,
                uniqueAuthorsInBatch,
                batchCoreDevs,
                self.__config,
            )
            
            results.append(self.__smellDetectionModule(batchIdx, batchDate))

        return results
    
    def __smellDetectionModule(self, batchIdx, batchDate):
        detectedSmells = None
        result = {}
        # run smell detection
        detectedSmells = smellDetection(self.__config, batchIdx)

        # building a dictionary of detected community smells for each batch analyzed
        result["Index"] = batchIdx
        result["StartingDate"] = batchDate.strftime("%m/%d/%Y")

        # separating smells and converting in their full name
        for index, smell in enumerate(detectedSmells):
            if(index != 0):
                smellName = "Smell" + str(index)
                result[smellName] = [
                    smell, get_community_smell_name(detectedSmells[index])]
        add_to_smells_dataset(
            self.__config, batchDate.strftime("%m/%d/%Y"), detectedSmells)
    

        return detectedSmells, result

    def getCommunitySmells(self):
        commits = self.__mineDevelopersAliases()
        authorInfoDict, batchDates, coreDevs, prParticipantBatches, issueParticipantBatches = self.__buildSocialNetworkGraphs(commits)
        result = self.__computSentimentsMetrics(authorInfoDict, batchDates, prParticipantBatches, issueParticipantBatches, coreDevs)
        detectedSmells, detectedSmellsDict = result[0]
        return detectedSmells, detectedSmellsDict, self.__config

communitySmells = [
    {"acronym": "OSE", "name": "Organizational Silo Effect"},
    {"acronym": "BCE", "name": "Black-cloud Effect"},
    {"acronym": "PDE", "name": "Prima-donnas Effect"},
    {"acronym": "SV", "name": "Sharing Villainy"},
    {"acronym": "OS", "name": "Organizational Skirmish"},
    {"acronym": "SD", "name": "Solution Defiance "},
    {"acronym": "RS", "name": "Radio Silence"},
    {"acronym": "TF", "name": "Truck Factor Smell"},
    {"acronym": "UI", "name": "Unhealthy Interaction"},
    {"acronym": "TC", "name": "Toxic Communication"},
]

# converting community smell acronym in full name
def get_community_smell_name(smell):
    for sm in communitySmells:
        if sm["acronym"] == smell:
            return sm["name"]
    return smell

# collecting execution data into a dataset
def add_to_smells_dataset(config, starting_date, detected_smells):
    with pd.ExcelWriter('./communitySmellsDataset.xlsx', engine="openpyxl", mode='a', if_sheet_exists="overlay") as writer:
        dataframe = pd.DataFrame(index=[writer.sheets['dataset'].max_row],
                                 data={'repositoryUrl': [config.repositoryUrl],
                                       'repositoryName': [config.repositoryName],
                                       'repositoryAuthor': [config.repositoryOwner],
                                       'startingDate': [starting_date],
                                       'OSE': [str(detected_smells.count('OSE'))],
                                       'BCE': [str(detected_smells.count('BCE'))],
                                       'PDE': [str(detected_smells.count('PDE'))],
                                       'SV': [str(detected_smells.count('SV'))],
                                       'OS': [str(detected_smells.count('OS'))],
                                       'SD': [str(detected_smells.count('SD'))],
                                       'RS': [str(detected_smells.count('RS'))],
                                       'TFS': [str(detected_smells.count('TFS'))],
                                       'UI': [str(detected_smells.count('UI'))],
                                       'TC': [str(detected_smells.count('TC'))]
                                       })
        dataframe.to_excel(writer, sheet_name="dataset",
                           startrow=writer.sheets['dataset'].max_row, header=False)


