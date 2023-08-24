import os

from csdetector import Configuration, utils
from csdetector.metrics.authorAlias import AuthorAlias

class CSFactory:
    def __init__(self, config: Configuration):
        self._config = config
        
        # prepare folders
        if os.path.exists(self._config.resultsPath):
            utils.remove_tree(self._config.resultsPath)

        os.makedirs(self._config.metricsPath)

        # get repository reference
        self._repo = utils.getRepo(self._config)

    def detect(self):
        authorAliasExtractor = AuthorAlias(self._config)
        authorAlias = authorAliasExtractor.extract()
        print(authorAlias)
        return ['a', 'b', 'c']
