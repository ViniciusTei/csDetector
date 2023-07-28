import os
import yaml
import logging
from progress.bar import Bar
from lib.utils import authorIdExtractor
from lib.configuration import Configuration

def replaceAliases(commits, config: Configuration):
    logging.info("Cleaning aliased authors")

    # build path
    aliasPath = os.path.join(config.repositoryPath, "aliases.yml")

    # quick lowercase and trim if no alias file
    if aliasPath == None or not os.path.exists(aliasPath):
        return commits

    # read aliases
    content = ""
    with open(aliasPath, "r", encoding="utf-8-sig") as file:
        content = file.read()

    aliases = yaml.load(content, Loader=yaml.FullLoader)

    # transpose for easy replacements
    transposesAliases = {}
    for alias in aliases:
        for email in aliases[alias]:
            transposesAliases[email] = alias

    # replace all author aliases with a unique one
    return replaceAll(commits, transposesAliases)


def replaceAll(commits, aliases):
    for commit in Bar("Processing").iter(list(commits)):
        copy = commit
        author = authorIdExtractor(commit.author)

        if author in aliases:
            copy.author.email = aliases[author]

        yield copy
