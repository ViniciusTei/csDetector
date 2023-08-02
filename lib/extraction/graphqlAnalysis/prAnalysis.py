import math
import graphene
import os
import csv
import sys
import sentistrength
import threading
import logging
from dateutil.parser import isoparse
from typing import List
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from lib.extraction.perspectiveAnalysis import getToxicityPercentage
from lib.extraction.statsAnalysis import outputStatistics 
from lib.extraction.graphqlAnalysis.graphqlAnalysisHelper import buildNextPageQuery, addLogin, runGraphqlRequest
from lib.extraction.centralityAnalysis import buildGraphQlNetwork 
from lib.configuration import Configuration

def prAnalysis(
    config: Configuration,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batchDates: List[datetime],
):

    logging.info("Querying PRs")
    batches = prRequest(
        config.pat, config.repositoryOwner, config.repositoryName, delta, batchDates
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


def analyzeSentiments(
    senti, comments, positiveComments, negativeComments, generallyNegative, semaphore
):
    with semaphore:
        commentSentiments = (
            senti.getSentiment(comments, score="scale")
            if len(comments) > 1
            else senti.getSentiment(comments[0])
        )

        commentSentimentsPositive = sum(
            1 for _ in filter(lambda value: value >= 1, commentSentiments)
        )
        commentSentimentsNegative = sum(
            1 for _ in filter(lambda value: value <= -1, commentSentiments)
        )

        lock = threading.Lock()
        with lock:
            positiveComments.append(commentSentimentsPositive)
            negativeComments.append(commentSentimentsNegative)

            if commentSentimentsNegative / len(comments) > 0.5:
                generallyNegative.append(True)

            logging.info(f".", end="")


def prRequest(
    pat: str, owner: str, name: str, delta: relativedelta, batchDates: List[datetime]
):
    query = buildPrRequestQuery(owner, name, None)

    # prepare batches
    batches = []
    batch = []
    batchStartDate = None
    batchEndDate = None

    while True:

        # get page
        schema = graphene.Schema(query=PullRequestsQuery)
        result = schema.execute(query)
        logging.info(f"Quering Pull Requests GraphQL")

        if result.errors:
            logging.error(f'GraphQL Error: {result.errors}')
            break

        # extract nodes
        nodes = result.data["repository"]["pullRequests"]["nodes"]

        # add results
        for node in nodes:

            createdAt = isoparse(node["createdAt"])
            closedAt = (
                datetime.now(timezone.utc)
                if node["closedAt"] is None
                else isoparse(node["closedAt"])
            )

            if batchEndDate == None or (
                createdAt > batchEndDate and len(batches) < len(batchDates) - 1
            ):

                if batch != None:
                    batches.append(batch)

                batchStartDate = batchDates[len(batches)]
                batchEndDate = batchStartDate + delta

                batch = []

            pr = {
                "number": node["number"],
                "createdAt": createdAt,
                "closedAt": closedAt,
                "comments": list(c["bodyText"] for c in node["comments"]["nodes"]),
                "commitCount": node["commits"]["totalCount"],
                "participants": list(),
            }

            # participants
            for user in node["participants"]["nodes"]:
                addLogin(user, pr["participants"])

            batch.append(pr)

        # check for next page
        pageInfo = result.data["repository"]["pullRequests"]["pageInfo"]
        if not pageInfo["hasNextPage"]:
            break

        cursor = pageInfo["endCursor"]
        query = buildPrRequestQuery(owner, name, cursor)

    if batch != None:
        batches.append(batch)

    return batches

class Participant(graphene.ObjectType):
    login = graphene.String()

class Comment(graphene.ObjectType):
    bodyText = graphene.String()

class PullRequest(graphene.ObjectType):
    number = graphene.Int()
    createdAt = graphene.String()
    closedAt = graphene.String()
    participants = graphene.List(Participant)
    commits = graphene.Field(graphene.Int)
    comments = graphene.List(Comment)

class PageInfo(graphene.ObjectType):
    endCursor = graphene.String()
    hasNextPage = graphene.Boolean()

class PullRequestsQuery(graphene.ObjectType):
    repository = graphene.Field(
        PullRequest,
        owner=graphene.String(required=True),
        name=graphene.String(required=True),
    )

    def resolve_repository(self, info, owner, name):
        query = buildPrRequestQuery(owner, name, info.context.get('cursor'))
        return runGraphqlRequest(info.context.get('access_token'), query)
         

def buildPrRequestQuery(owner: str, name: str, cursor):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            pullRequests(first:40{2}) {{
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                nodes {{
                    number
                    createdAt
                    closedAt
                    participants(first: 50) {{
                        nodes {{
                            login
                        }}
                    }}
                    commits {{
                        totalCount
                    }}
                    comments(first: 20) {{
                        nodes {{
                            bodyText
                        }}
                    }}
                }}
            }}
        }}
    }}
    """.format(
        owner, name,buildNextPageQuery(cursor)
    )
