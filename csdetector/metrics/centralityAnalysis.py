import csv
import logging
import os
from datetime import datetime
from typing import List
from collections import Counter
from dateutil.relativedelta import relativedelta
import networkx as nx
from git import Commit
import matplotlib.pyplot as plt
from csdetector import Configuration
from csdetector.github.GitHubRequestHelper import GitHubRequestHelper
from csdetector.utils.statistics import outputStatistics
from networkx.algorithms.community import greedy_modularity_communities

class CentralityAnalysis:
    def __init__(self, config: Configuration, commits: List[Commit], delta: relativedelta, batchDates: List[datetime]):
        self._config = config
        self._commits = commits
        self._delta = delta
        self._batchDates = batchDates
        pass

    def extract(self):
        coreDevs = list()
        logging.info("Starting centrality analysis for {}".format(self._batchDates))

        for idx, batchStartDate in enumerate(self._batchDates):
            logging.info("Batch {} with start date {}".format(idx, batchStartDate))
            batchEndDate = batchStartDate + self._delta
            batch = [c for c in self._commits if c.committed_datetime >= batchStartDate and c.committed_datetime < batchEndDate]
            logging.info("Processing batch {} with {} commits".format(idx, len(batch)))

            batchCoreDevs = self._processBatch(idx, batch)

            coreDevs.append(batchCoreDevs)

        logging.info("Finished centrality analysis, returning {} core devs".format(len(coreDevs)))
        return coreDevs

    def buildGraph(self, batchIdx: int, batch: list, prefix: str):
        allRelatedAuthors = {}
        authorItems = Counter({})

        # for all commits...
        print("Analyzing centrality")
        for authors in batch:

            for author in authors:

                # increase author commit count
                authorItems.update({author: 1})

                # get current related authors collection and update it
                relatedAuthors = set(
                    relatedAuthor
                    for otherAuthors in batch
                    for relatedAuthor in otherAuthors
                    if author in otherAuthors and relatedAuthor != author
                )
                authorRelatedAuthors = allRelatedAuthors.setdefault(author, set())
                authorRelatedAuthors.update(relatedAuthors)

        return self._prepareGraph(allRelatedAuthors, authorItems, batchIdx, prefix)

    def _processBatch(self, batchIdx: int, commits: List[Commit]):
        allRelatedAuthors = {}
        authorCommits = Counter({})

        for commit in commits:
            author = GitHubRequestHelper.get_author_id(commit.author)

            authorCommits.update({ author: 1 })

            commitDate = datetime.fromtimestamp(commit.committed_date)
            earliestDate = commitDate + relativedelta(months=-1)
            latestDate = commitDate + relativedelta(months=+1)

            commitRelatedCommits = filter(
                lambda c: self._findRelatedCommits(author, earliestDate, latestDate, c), commits
            )

            commitRelatedAuthors = set(
                list(map(lambda c: GitHubRequestHelper.get_author_id(c.author), commitRelatedCommits))
            )

            # get current related authors collection and update it
            authorRelatedAuthors = allRelatedAuthors.setdefault(author, set())
            authorRelatedAuthors.update(commitRelatedAuthors)
        return self._prepareGraph(allRelatedAuthors, authorCommits, batchIdx, "commitCentrality")

    def _prepareGraph(self,allRelatedAuthors: dict, authorItems: Counter, batchIdx: int, outputPrefix: str):
        G = nx.Graph()
        logging.info("Preparing graph for batch {} with {} authors".format(batchIdx, len(allRelatedAuthors)))
        for author in allRelatedAuthors:
            G.add_node(author)

            for relatedAuthor in allRelatedAuthors[author]:
                G.add_edge(author.strip(), relatedAuthor.strip())

        # analyze graph
        closeness = dict(nx.closeness_centrality(G))
        betweenness = dict(nx.betweenness_centrality(G))
        centrality = dict(nx.degree_centrality(G))
        density = nx.density(G)
        modularity = []

        try:
            for idx, community in enumerate(greedy_modularity_communities(G)):
                authorCount = len(community)
                communityCommitCount = sum(authorItems[author] for author in community)
                row = [authorCount, communityCommitCount]
                modularity.append(row)
        except ZeroDivisionError:
            # not handled
            pass

        # finding high centrality authors
        highCentralityAuthors = list(
            [author for author, centrality in centrality.items() if centrality > 0.5]
        )

        numberHighCentralityAuthors = len(highCentralityAuthors)

        percentageHighCentralityAuthors = numberHighCentralityAuthors / len(
            allRelatedAuthors
        )

        # calculate TFN
        tfn = len(authorItems) - numberHighCentralityAuthors

        # calculate TFC
        tfc = sum(authorItems[author] for author in highCentralityAuthors) / sum(authorItems.values()) * 100


        logging.info("Outputting csv files for batch {}".format(batchIdx))
        # output non-tabular results
        with open(
            os.path.join(self._config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow([f"{outputPrefix}_Density", density])
            w.writerow([f"{outputPrefix}_Community Count", len(modularity)])
            w.writerow([f"{outputPrefix}_TFN", tfn])
            w.writerow([f"{outputPrefix}_TFC", tfc])

        # output community information
        with open(
            os.path.join(self._config.metricsPath, f"{outputPrefix}_community_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Community Index", "Author Count", "Item Count"])
            for idx, community in enumerate(modularity):
                w.writerow([idx + 1, community[0], community[1]])

        # combine centrality results
        combined = {}
        for key in closeness:
            single = {
                "Author": key,
                "Closeness": closeness[key],
                "Betweenness": betweenness[key],
                "Centrality": centrality[key],
            }

            combined[key] = single

        # output tabular results
        with open(
            os.path.join(self._config.metricsPath, f"{outputPrefix}_centrality_{batchIdx}.csv"),
            "w",
            newline="",
        ) as f:
            w = csv.DictWriter(f, ["Author", "Closeness", "Betweenness", "Centrality"])
            w.writeheader()

            for key in combined:
                w.writerow(combined[key])

        # output high centrality authors
        with open(
            os.path.join(self._config.resultsPath, f"results_{batchIdx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(
                [f"{outputPrefix}_NumberHighCentralityAuthors", numberHighCentralityAuthors]
            )
            w.writerow(
                [
                    f"{outputPrefix}_PercentageHighCentralityAuthors",
                    percentageHighCentralityAuthors,
                ]
            )

        # output statistics
        outputStatistics(
            batchIdx,
            [value for key, value in closeness.items()],
            f"{outputPrefix}_Closeness",
            self._config.resultsPath,
        )

        outputStatistics(
            batchIdx,
            [value for key, value in betweenness.items()],
            f"{outputPrefix}_Betweenness",
            self._config.resultsPath,
        )

        outputStatistics(
            batchIdx,
            [value for key, value in centrality.items()],
            f"{outputPrefix}_Centrality",
            self._config.resultsPath,
        )

        outputStatistics(
            batchIdx,
            [community[0] for community in modularity],
            f"{outputPrefix}_CommunityAuthorCount",
            self._config.resultsPath,
        )

        outputStatistics(
            batchIdx,
            [community[1] for community in modularity],
            f"{outputPrefix}_CommunityAuthorItemCount",
            self._config.resultsPath,
        )

        # output graph
        print("Outputting graph")
        plt.figure(5, figsize=(30, 30))

        nx.draw(
            G,
            with_labels=True,
            node_color="orange",
            node_size=4000,
            edge_color="black",
            linewidths=2,
            font_size=20,
        )

        plt.savefig(
            os.path.join(self._config.resultsPath, f"{outputPrefix}_{batchIdx}.pdf")
        )

        nx.write_graphml(
            G, os.path.join(self._config.resultsPath, f"{outputPrefix}_{batchIdx}.xml")
        )

        return highCentralityAuthors
    
    def _findRelatedCommits(self, author, earliestDate, latestDate, commit):
        isDifferentAuthor = author != GitHubRequestHelper.get_author_id(commit.author)
        if not isDifferentAuthor:
            return False

        commitDate = datetime.fromtimestamp(commit.committed_date)
        isInRange = commitDate >= earliestDate and commitDate <= latestDate
        return isInRange
