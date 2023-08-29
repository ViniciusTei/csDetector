import git
import shutil
import os
import stat

from csdetector import Configuration

def remove_readonly(fn, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    remove_tree(path)


def remove_tree(path):
    if os.path.isdir(path):
        shutil.rmtree(path, onerror=remove_readonly)
    else:
        os.remove(path)

def authorIdExtractor(author: git.Actor):
    id = ""

    if author.email is None:
        id = author.name
    else:
        id = author.email

    id = id.lower().strip()
    return id

def iterLen(obj: iter):
    return sum(1 for _ in obj)

def getRepo(config: Configuration):
    # build path
    repoPath = os.path.join(
        config.repositoryPath,
        "{}.{}".format(config.repositoryOwner, config.repositoryName),
    )
    # get repository reference
    repo = None
    fullRepoPath = os.path.join(os.getcwd(), repoPath)
    if not os.path.exists(fullRepoPath):
        print("Downloading repository...")
        repo = git.Repo.clone_from(
            config.repositoryUrl,
            repoPath,
            progress=Progress(),
            odbt=git.GitCmdObjectDB,
        )
        print()
    else:
        repo = git.Repo(repoPath, odbt=git.GitCmdObjectDB)
    return repo



class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=""):
        print(self._cur_line, end="\r")
