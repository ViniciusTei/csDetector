import sys
import pkg_resources
import logging
import datetime
import os

from csdetector.communitysmells import CommunitySmells
from csdetector.config import initialize_config

# define logging 
def generate_filename_with_datetime():
    current_datetime = datetime.datetime.now()
    formated_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{formated_datetime}.txt"
    abs_path = os.path.abspath(f"logs/{filename}")
    return abs_path

LOG_FILENAME=generate_filename_with_datetime()

if __name__ == "__main__":
    # validate running in venv
    if not hasattr(sys, "prefix"):
        raise Exception(
            "The tool does not appear to be running in the virtual environment!\nSee README for activation."
        )

    # validate python version
    if sys.version_info.major != 3 or sys.version_info.minor != 10:
        raise Exception(
            "Expected Python 3.10 as runtime but got {0}.{1}, the tool might not run as expected!\nSee README for stack requirements.".format(
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
            )
        )

    # validate installed modules
    required = {
        "wheel",
        "networkx",
        "pandas",
        "matplotlib",
        "gitpython",
        "requests",
        "pyyaml",
        "progress",
        "strsimpy",
        "python-dateutil",
        "sentistrength",
        "joblib",
    }

    installed = {pkg for pkg in pkg_resources.working_set.by_key}
    missing = required - installed

    if len(missing) > 0:
        raise Exception(
            "Missing required modules: {0}.\nSee README for tool installation.".format(
                missing
            )
        )

    args = sys.argv[1:]
    global_configuration, DEBUG = initialize_config(args)

    logging.basicConfig(
        filename=LOG_FILENAME, 
        level=DEBUG and logging.DEBUG or logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logging.debug("Started with DEBUG mode enabled")
    logging.info("CsDetector started, analysing repository: {0}".format(global_configuration.repositoryUrl))

    smells = CommunitySmells(global_configuration).detect()
    logging.info("CsDetector finished, found {0} smells.".format(len(smells)))
    print(smells)
    
