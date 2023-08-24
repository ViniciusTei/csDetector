import os

# a singleton class to hold the tool configuration
# this class is used to pass the configuration to the other modules
# this class is also used to build the paths to the repository and the results
class Configuration:
    def __init__(
        self,
        repositoryUrl: str,
        batchMonths: int,
        outputPath: str,
        sentiStrengthPath: str,
        maxDistance: int,
        pat: str,
        googleKey: str,
        startDate: str
    ):
        self.repositoryUrl = repositoryUrl
        self.batchMonths = batchMonths
        self.outputPath = outputPath
        self.sentiStrengthPath = sentiStrengthPath
        self.maxDistance = maxDistance
        self.googleKey = googleKey
        self.startDate = startDate

        # parse more than 1 token if it exists
        if "," in pat:
            self.pat = pat.split(",")
        else:
            self.pat = [pat]

        # parse repo name into owner and project name
        split = self.repositoryUrl.split("/")
        self.repositoryOwner = split[3]
        self.repositoryName = split[4]

        # build repo path
        self.repositoryPath = os.path.join(self.outputPath, split[3], split[4])

        # build results path
        self.resultsPath = os.path.join(self.repositoryPath, "results")

        # build metrics path
        self.metricsPath = os.path.join(self.resultsPath, "metrics")

