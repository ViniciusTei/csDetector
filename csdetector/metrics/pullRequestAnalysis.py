import csv
import os
import logging
import math
import sys
import threading
from datetime import datetime, timezone
from typing import List
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import sentistrength
from csdetector import Configuration
from csdetector.entities.PullRequest import PullRequest
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.github.GitHubRequestPullRequest import GitHubRequestPullRequest
from csdetector.metrics.commitAnalysis import outputStatistics

class PRAnalysis:
    _request: GitHubRequestController
    _config: Configuration

    def __init__(self, config: Configuration) -> None:
        self._config = config
        self._request = GitHubRequestController(self._config)
        self._request.init(strategy=GitHubRequestPullRequest())
        pass

    @classmethod
    def _prRequest(cls, delta: relativedelta, batchDates: List[datetime]):
        pages = cls._request.numberOfPages(cls._config) 
        
        # prepare batches
        batches = []
        batch = None
        batchStartDate = None
        batchEndDate = None
        for page in range(1, pages + 1):
            logging.info("Querying page {}".format(page))
            response = cls._request.requestPerPage(cls._config, page) 

            if response is not None:
                responseData = response.json()
                for data in responseData:
                    createdAt = isoparse(data["created_at"])
                    closedAt = (
                        datetime.now(timezone.utc)
                        if data["closed_at"] is None
                        else isoparse(data["closed_at"])
                    )

                    if batchEndDate == None or (
                        createdAt > batchEndDate and len(batches) < len(batchDates) - 1
                    ):

                        if batch != None:
                            batches.append(batch)

                        batchStartDate = batchDates[len(batches)]
                        batchEndDate = batchStartDate + delta

                        batch = []

                    comments = cls._request.requestComments(data["comments_url"])
                    participants = cls._request.requestParticipants(cls._config, data["number"])

                    pr = PullRequest(
                        number=data["number"],
                        createdAt=createdAt,
                        closedAt=closedAt,
                        comments=comments,
                        commitCount=data["commits"],
                        participants=participants
                    )

                    batch.append(pr)

        return batches

    @classmethod
    def extract(cls, senti: sentistrength.PySentiStr, delta: relativedelta,batchDates: List[datetime]):

        logging.info("Querying PRs")
        batches = cls._prRequest(
            delta, batchDates
        )

        batchParticipants = list()
        batchComments = list()

        for batchIdx, batch in enumerate(batches):
            logging.info(f"Analyzing PR batch #{batchIdx}")

            # extract data from batch
            prCount = len(batch)
            participants = list(
                pr["participants"] for pr in batch if len(pr["participants"]) > 0
            )
            batchParticipants.append(participants)

            allComments = list()
            prPositiveComments = list()
            prNegativeComments = list()
            generallyNegative = list()

            logging.info(f"Sentiments per PR")

            semaphore = threading.Semaphore(15)
            threads = []
            for pr in batch:

                comments = list(
                    comment for comment in pr["comments"] if comment and comment.strip()
                )

                # split comments that are longer than 20KB
                splitComments = []
                for comment in comments:

                    # calc number of chunks
                    byteChunks = math.ceil(sys.getsizeof(comment) / (20 * 1024))
                    if byteChunks > 1:

                        # calc desired max length of each chunk
                        chunkLength = math.floor(len(comment) / byteChunks)

                        # divide comment into chunks
                        chunks = [
                            comment[i * chunkLength : i * chunkLength + chunkLength]
                            for i in range(0, byteChunks)
                        ]

                        # save chunks
                        splitComments.extend(chunks)

                    else:
                        # append comment as-is
                        splitComments.append(comment)

                # re-assign comments after chunking
                comments = splitComments

                if len(comments) == 0:
                    prPositiveComments.append(0)
                    prNegativeComments.append(0)
                    continue

                allComments.extend(comments)

                thread = threading.Thread(
                    target=analyzeSentiments,
                    args=(
                        senti,
                        comments,
                        prPositiveComments,
                        prNegativeComments,
                        generallyNegative,
                        semaphore,
                    ),
                )
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            logging.info("")

            # save comments
            batchComments.append(allComments)

            # get comment length stats
            commentLengths = [len(c) for c in allComments]

            generallyNegativeRatio = len(generallyNegative) / prCount

            # get pr duration stats
            durations = [(pr["closedAt"] - pr["createdAt"]).days for pr in batch]

            logging.info("Analyzing PR batch  All sentiments")

            commentSentiments = []
            commentSentimentsPositive = 0
            commentSentimentsNegative = 0

            if len(allComments) > 0:
                commentSentiments = senti.getSentiment(allComments)
                commentSentimentsPositive = sum(
                    1 for _ in filter(lambda value: value >= 1, commentSentiments)
                )
                commentSentimentsNegative = sum(
                    1 for _ in filter(lambda value: value <= -1, commentSentiments)
                )

            toxicityPercentage = getToxicityPercentage(config, allComments)

            buildGraphQlNetwork(batchIdx, participants, "PRs", config)

            logging.info("  Analyzing PR batch  Writing results")
            with open(
                os.path.join(config.resultsPath, f"results_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["NumberPRs", prCount])
                w.writerow(["NumberPRComments", len(allComments)])
                w.writerow(["PRCommentsPositive", commentSentimentsPositive])
                w.writerow(["PRCommentsNegative", commentSentimentsNegative])
                w.writerow(["PRCommentsNegativeRatio", generallyNegativeRatio])
                w.writerow(["PRCommentsToxicityPercentage", toxicityPercentage])

            with open(
                os.path.join(config.metricsPath, f"PRCommits_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["PR Number", "Commit Count"])
                for pr in batch:
                    w.writerow([pr["number"], pr["commitCount"]])

            with open(
                os.path.join(config.metricsPath, f"PRParticipants_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["PR Number", "Developer Count"])
                for pr in batch:
                    w.writerow([pr["number"], len(set(pr["participants"]))])

            # output statistics
            outputStatistics(
                batchIdx,
                commentLengths,
                "PRCommentsLength",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                durations,
                "PRDuration",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [len(pr["comments"]) for pr in batch],
                "PRCommentsCount",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [pr["commitCount"] for pr in batch],
                "PRCommitsCount",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                commentSentiments,
                "PRCommentSentiments",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [len(set(pr["participants"])) for pr in batch],
                "PRParticipantsCount",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                prPositiveComments,
                "PRCountPositiveComments",
                config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                prNegativeComments,
                "PRCountNegativeComments",
                config.resultsPath,
            )

        return batchParticipants, batchComments
        pass
