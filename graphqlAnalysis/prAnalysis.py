import os
import csv
import statsAnalysis as stats
import sentistrength
import graphqlAnalysis.graphqlAnalysisHelper as gql
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
from typing import List
from datetime import datetime
from configuration import Configuration
import itertools
import threading


def prAnalysis(
    config: Configuration,
    pat: str,
    senti: sentistrength.PySentiStr,
    delta: relativedelta,
    batchDates: List[datetime],
):

    # split repo by owner and name
    owner, name = gql.splitRepoName(config.repositoryShortname)

    print("Querying PRs")
    batches = prRequest(pat, owner, name, delta, batchDates)

    participantBatches = list()

    for batchIdx, batch in enumerate(batches):
        print(f"Analyzing PR batch #{batchIdx}")

        # extract data from batch
        prCount = len(batch)
        participants = set(p for pr in batch for p in pr["participants"])
        participantBatches.append(participants)

        allComments = list()
        prPositiveComments = list()
        prNegativeComments = list()

        print(f"    Sentiments per PR", end="")

        semaphore = threading.Semaphore(255)
        threads = []
        for pr in batch:

            prComments = pr["comments"]

            if len(prComments) == 0:
                prPositiveComments.append(0)
                prNegativeComments.append(0)
                continue

            allComments.extend(prComments)

            thread = threading.Thread(
                target=analyzeSentiments,
                args=(
                    senti,
                    prComments,
                    prPositiveComments,
                    prNegativeComments,
                    semaphore,
                ),
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        print("")

        print("    All sentiments")

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

        print("    Writing results")
        with open(
            os.path.join(config.analysisOutputPath, f"project_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["NumberPRs", prCount])
            w.writerow(["NumberPRComments", len(allComments)])
            w.writerow(["PRCommentsPositive", commentSentimentsPositive])
            w.writerow(["PRCommentsNegative", commentSentimentsNegative])

        with open(
            os.path.join(config.analysisOutputPath, f"PRCommits_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Commit Count"])
            for pr in batch:
                w.writerow([pr["number"], pr["commitCount"]])

        with open(
            os.path.join(config.analysisOutputPath, f"PRParticipants_{batchIdx}.csv"),
            "a",
            newline="",
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["PR Number", "Developer Count"])
            for pr in batch:
                w.writerow([pr["number"], len(pr["participants"])])

        # output statistics
        stats.outputStatistics(
            batchIdx,
            [len(pr["comments"]) for pr in batch],
            "PRCommentsCount",
            config.analysisOutputPath,
        )

        stats.outputStatistics(
            batchIdx,
            [pr["commitCount"] for pr in batch],
            "PRCommitsCount",
            config.analysisOutputPath,
        )

        stats.outputStatistics(
            batchIdx,
            commentSentiments,
            "PRCommentSentiments",
            config.analysisOutputPath,
        )

        stats.outputStatistics(
            batchIdx,
            [len(pr["participants"]) for pr in batch],
            "PRParticipantsCount",
            config.analysisOutputPath,
        )

        stats.outputStatistics(
            batchIdx,
            prPositiveComments,
            "PRCountPositiveComments",
            config.analysisOutputPath,
        )

        stats.outputStatistics(
            batchIdx,
            prNegativeComments,
            "PRCountNegativeComments",
            config.analysisOutputPath,
        )

    return participantBatches


def analyzeSentiments(
    senti, prComments, prPositiveComments, prNegativeComments, semaphore
):
    with semaphore:
        commentSentiments = senti.getSentiment(prComments)
        commentSentimentsPositive = sum(
            1 for _ in filter(lambda value: value >= 1, commentSentiments)
        )
        commentSentimentsNegative = sum(
            1 for _ in filter(lambda value: value <= -1, commentSentiments)
        )

        lock = threading.Lock()
        with lock:
            prPositiveComments.append(commentSentimentsPositive)
            prNegativeComments.append(commentSentimentsNegative)
            print(f".", end="")


def prRequest(
    pat: str, owner: str, name: str, delta: relativedelta, batchDates: List[datetime]
):
    query = buildPrRequestQuery(owner, name, None)

    # prepare batches
    batches = []
    batch = None
    batchStartDate = None
    batchEndDate = None

    while True:

        # get page
        result = gql.runGraphqlRequest(pat, query)
        print("...")

        # extract nodes
        nodes = result["repository"]["pullRequests"]["nodes"]

        # add results
        for node in nodes:

            createdAt = isoparse(node["createdAt"])

            if batchEndDate == None or createdAt > batchEndDate:

                if batch != None:
                    batches.append(batch)

                batchStartDate = batchDates[len(batches)]
                batchEndDate = batchStartDate + delta

                batch = []

            pr = {
                "number": node["number"],
                "createdAt": createdAt,
                "comments": list(c["bodyText"] for c in node["comments"]["nodes"]),
                "commitCount": node["commits"]["totalCount"],
                "participants": set(),
            }

            prParticipantCount = 0

            # author
            if gql.tryAddLogin(node["author"], pr["participants"]):
                prParticipantCount += 1

            # editor
            if gql.tryAddLogin(node["editor"], pr["participants"]):
                prParticipantCount += 1

            # assignees
            for user in node["assignees"]["nodes"]:
                if gql.tryAddLogin(user, pr["participants"]):
                    prParticipantCount += 1

            # participants
            for user in node["participants"]["nodes"]:
                if gql.tryAddLogin(user, pr["participants"]):
                    prParticipantCount += 1

            batch.append(pr)

        # check for next page
        pageInfo = result["repository"]["pullRequests"]["pageInfo"]
        if not pageInfo["hasNextPage"]:
            break

        cursor = pageInfo["endCursor"]
        query = buildPrRequestQuery(owner, name, cursor)

    if batch != None:
        batches.append(batch)

    return batches


def buildPrRequestQuery(owner: str, name: str, cursor: str):
    return """{{
        repository(owner: "{0}", name: "{1}") {{
            pullRequests(first:100{2}) {{
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                nodes {{
                    number
                    createdAt
                    author {{
                        ... on User {{
                            login
                        }}
                    }}
                    editor {{
                        ... on User {{
                            login
                        }}
                    }}
                    assignees(first: 100) {{
                        nodes {{
                            login
                        }}
                    }}
                    participants(first: 100) {{
                        nodes {{
                            login
                        }}
                    }}
                    commits {{
                        totalCount
                    }}
                    comments(first: 100) {{
                        nodes {{
                            bodyText
                        }}
                    }}
                }}
            }}
        }}
    }}
    """.format(
        owner, name, gql.buildNextPageQuery(cursor)
    )
