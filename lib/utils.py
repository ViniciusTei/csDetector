import git
import shutil
import os
import stat

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

