import argparse
import os
from urllib.parse import urlparse

from csdetector import Configuration

def initialize_config(entry_args: list[str]):
    parser = argparse.ArgumentParser(
        description="Perform network and statistical analysis on GitHub repositories.",
        epilog="Check README file for more information on running this tool.",
    )
    
    parser.add_argument(
        "-p",
        "--pat",
        help="GitHub PAT (personal access token) used for querying the GitHub API. If you are trying to analyze repos with massive data, you may need to use multiple PAT`s. Check the README for more details.",
        required=True,
    )

    parser.add_argument(
        "-g",
        "--googleKey",
        help="Google Cloud API Key used for authentication with the Perspective API",
        required=False,
    )

    parser.add_argument(
        "-r",
        "--repositoryUrl",
        help="GitHub repository URL that you want to analyse",
        required=True,
    )

    parser.add_argument(
        "-m",
        "--batchMonths",
        help="Number of months to analyze per batch. Default=9999",
        type=float,
        default=9999,
    )

    parser.add_argument(
        "-s",
        "--sentiStrengthPath",
        help="local directory path to the SentiStregth tool",
        required=True,
    )

    parser.add_argument(
        "-o",
        "--outputPath",
        help="Local directory path for analysis output",
        required=True,
    )

    parser.add_argument(
        "-sd",
        "--startDate",
        help="Start date of project life",
        required=False,
    )
    
    parser.add_argument(
        "-d",
        "--debug",
        help="Enable debug logging",
        required=False,
        nargs="?",
        const=True,
        default=False,
        type=bool,
    )

    parser.add_argument(
        "-a",
        "--alias",
        help="Extract authors alias for the repository",
        required=False,
        default=False,
        type=bool,
    )
    
    args = parser.parse_args(entry_args)

    #validation of the input inserted by the user
    if args.repositoryUrl is None:
        raise ValueError("The repository URL is needed")

    if "github" not in urlparse(args.repositoryUrl).netloc:
        raise ValueError("The repository URL inserted is not valid or malformed")

    if args.pat is None:
        raise ValueError("A valid Github PAT is needed to clone the repository")

    senti_files_found = False

    if args.sentiStrengthPath is None:
        raise ValueError("A valid senti folder is needed to perform sentiment analysis on the repository")

    try:
        with os.scandir(args.sentiStrengthPath) as entries:
            for entry in entries:
                if "SentiStrength" in entry.name:
                    senti_files_found = True
                    break
        if not senti_files_found:
            raise ValueError("The senti folder provided does not contains the needed files. Check the README for more "
                             "details")
    except FileNotFoundError:
        raise ValueError("A malformed or invalid senti folder is provided")

    if args.outputPath is None:
        raise ValueError("A valid output folder is needed to save the analysis of the repository")

    try:
        with os.scandir(args.outputPath) as entries:
            pass
    except FileNotFoundError:
        raise ValueError("The output folder provided is not avaiable in the file system or have restricted access")

    config = Configuration(
        args.repositoryUrl,
        args.batchMonths,
        args.outputPath,
        args.sentiStrengthPath,
        0,
        args.pat,
        args.googleKey,
        args.startDate,
        args.alias
    )

    return config, args.debug
