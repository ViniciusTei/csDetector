from datetime import datetime, timezone
import os
import csv
import logging
import math
import sys
import threading
from typing import List
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
import sentistrength
from csdetector import Configuration
from csdetector.entities.Issue import Issue
from csdetector.github.GitHubRequestController import GitHubRequestController
from csdetector.github.GitHubRequestIssues import GitHubRequestIssues
from csdetector.metrics.centralityAnalysis import CentralityAnalysis
from csdetector.metrics.commitAnalysis import outputStatistics
from csdetector.metrics.sentimentAnalysis import SentimentAnalysis

class IssueAnalysis:
    _request: GitHubRequestController
    _config: Configuration

    def __init__(self, config: Configuration, request: GitHubRequestController) -> None:
        self._config = config
        self._request = request
        self._request.setStrategy(strategy=GitHubRequestIssues)
        pass

    def extract(self, senti: sentistrength.PySentiStr, delta: relativedelta, batchDates: List[datetime], cA: CentralityAnalysis):
        batches = self._issueRequest(delta, batchDates)

        batchParticipants = list()
        batchComments = list()
        logging.info("Analyzing issues")

        for batchIdx, batch in enumerate(batches):
            logging.info(f"Analyzing issue batch #{batchIdx}")

            # extract data from batch
            issueCount = len(batch)
            participants = list(
                issue.participants for issue in batch if len(issue.participants) > 0
            )
            batchParticipants.append(participants)

            allComments = list()
            issuePositiveComments = list()
            issueNegativeComments = list()
            generallyNegative = list()

            semaphore = threading.Semaphore(15)
            threads = []
            for issue in batch:
                comments = list(
                    comment for comment in issue.comments if comment and comment.strip()
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
                    issuePositiveComments.append(0)
                    issueNegativeComments.append(0)
                    continue

                allComments.extend(comments)

                thread = threading.Thread(
                    target=SentimentAnalysis.analyze,
                    args=(
                        senti,
                        comments,
                        issuePositiveComments,
                        issueNegativeComments,
                        generallyNegative,
                        semaphore,
                    ),
                )
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            # save comments
            batchComments.append(allComments)

            # get comment length stats
            commentLengths = [len(c) for c in allComments]

            generallyNegativeRatio = len(generallyNegative) / issueCount

            durations = [(issue.closedAt - issue.createdAt).days for issue in batch]

            # analyze comment issue sentiment
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

            toxicityPercentage = SentimentAnalysis.getToxicityPercentage(self._config, allComments)

            cA.buildGraph(batchIdx, participants, "Issues")

            logging.info("Writing GraphQL analysis results")
            with open(
                os.path.join(self._config.resultsPath, f"results_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["NumberIssues", len(batch)])
                w.writerow(["NumberIssueComments", len(allComments)])
                w.writerow(["IssueCommentsPositive", commentSentimentsPositive])
                w.writerow(["IssueCommentsNegative", commentSentimentsNegative])
                w.writerow(["IssueCommentsNegativeRatio", generallyNegativeRatio])
                w.writerow(["IssueCommentsToxicityPercentage", toxicityPercentage])

            with open(
                os.path.join(self._config.metricsPath, f"issueCommentsCount_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["Issue Number", "Comment Count"])
                for issue in batch:
                    w.writerow([issue.number, len(issue.comments)])

            with open(
                os.path.join(self._config.metricsPath, f"issueParticipantCount_{batchIdx}.csv"),
                "a",
                newline="",
            ) as f:
                w = csv.writer(f, delimiter=",")
                w.writerow(["Issue Number", "Developer Count"])
                for issue in batch:
                    w.writerow([issue.number, len(set(issue.participants))])

            # output statistics
            outputStatistics(
                batchIdx,
                commentLengths,
                "IssueCommentsLength",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                durations,
                "IssueDuration",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [len(issue.comments) for issue in batch],
                "IssueCommentsCount",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                commentSentiments,
                "IssueCommentSentiments",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                [len(set(issue.participants)) for issue in batch],
                "IssueParticipantCount",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                issuePositiveComments,
                "IssueCountPositiveComments",
                self._config.resultsPath,
            )

            outputStatistics(
                batchIdx,
                issueNegativeComments,
                "IssueCountNegativeComments",
                self._config.resultsPath,
            )

        return batchParticipants, batchComments

    def _issueRequest(self, delta: relativedelta, batchDates: List[datetime]) -> List[List[Issue]]:
        # prepare batches
        batches = []
        batch = None
        batchStartDate = None
        batchEndDate = None

        pages = self._request.numberOfPages(self._config) 

        for page in range(1, pages + 1):
            logging.info("Querying page {}".format(page))
            response = self._request.requestPerPage(self._config, page) 

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

                    comments = self._request.requestComments(data["comments_url"])
                    participants = self._request.requestParticipants(self._config, data["number"])

                    issue = Issue(
                        number=data["number"],
                        createdAt=createdAt,
                        closedAt=closedAt,
                        comments=comments,
                        participants=participants,
                    )
                    
                    batch.append(issue)

        if batch != None:
            batches.append(batch)

        logging.info("Retrieved {} Issues".format(len(batches)))
        return batches
