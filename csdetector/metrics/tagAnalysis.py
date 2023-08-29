import csv
import logging
import os
import datetime
from typing import List
from dateutil.relativedelta import relativedelta

from csdetector.utils.statistics import outputStatistics

class TagAnalysis:
    def __init__(self, config, repo, delta: relativedelta, batchDates: List[datetime.datetime], daysActive: List[int]):
        self._config = config
        self._repo = repo
        self._delta = delta
        self._batchDates = batchDates
        self._daysActive = daysActive
        pass

    def extract(self):
        tagInfo = []
        tags = sorted(self._repo.tags, key=self._getTaggedDate)
        logging.info("Found {} tags".format(len(tags)))

        if len(tags) > 0:
            lastTag = None

            for tag in tags:
                commitCount = 0
                if lastTag is None:
                    commitCount = len(list(tag.commit.iter_items(self._repo, tag.commit)))
                else:
                    sinceStr = self._getTaggedDate(lastTag).strftime("%Y-%m-%d") 
                    commitCount = len(list(tag.commit.iter_items(self._repo, tag.commit, after=sinceStr)))

                tagInfo.append(
                    dict(
                        path=tag.path,
                        rawData=self._getTaggedDate(tag),
                        date=self._getTaggedDate(tag).strftime("%Y-%m-%d"),
                        commitCount=commitCount,
                    ) 
                )

                lastTag = tag

        for idx, batchStartDate in enumerate(self._batchDates):
            batchEndDate = batchStartDate + self._delta

            batchTags = [tag for tag in tagInfo if tag['rawData'] >= batchStartDate and tag['rawData'] < batchEndDate]

            self._outputTags(idx, batchTags, self._daysActive[idx])

    def _outputTags(self, idx: int, tagInfo: List[dict], daysActive: int):

        # calculate FN
        fn = len(tagInfo) / daysActive * 100

        # output non-tabular results
        with open(
            os.path.join(self._config.resultsPath, f"results_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Tag Count", len(tagInfo)])

        # output tag info
        logging.info("Outputting CSVs")

        with open(
            os.path.join(self._config.resultsPath, f"results_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["FN", fn])

        with open(
            os.path.join(self._config.metricsPath, f"tags_{idx}.csv"), "a", newline=""
        ) as f:
            w = csv.writer(f, delimiter=",")
            w.writerow(["Path", "Date", "Commit Count"])
            for tag in tagInfo:
                w.writerow([tag["path"], tag["date"], tag["commitCount"]])

        outputStatistics(
            idx,
            [tag["commitCount"] for tag in tagInfo],
            "TagCommitCount",
            self._config.resultsPath,
        )

    def _getTaggedDate(self, tag):
        date = None

        if tag.tag == None:
            date = tag.commit.committed_datetime
        else:

            # get timezone
            offset = tag.tag.tagger_tz_offset
            tzinfo = datetime.timezone(-datetime.timedelta(seconds=offset))

            # get aware date from timestamp
            date = tag.tag.tagged_date
            date = datetime.datetime.fromtimestamp(date, tzinfo)

        return date
