import os
import sentistrength
from git.repo import Repo

from csdetector import Configuration, utils
from csdetector.metrics.authorAlias import AuthorAlias

class CSFactory:
    _config: Configuration
    _repo: Repo
    _senti: sentistrength.PySentiStr

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

    def detect(self):
        authorAliasExtractor = AuthorAlias(self._config, self._repo)
        authorAlias = authorAliasExtractor.extract()
        print(authorAlias)
        return ['a', 'b', 'c']
