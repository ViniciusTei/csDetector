# CSDETECTOR - DOCS

## devNetwork

The code in this file conducts different analyses related to the project's development, such as commit analysis, centrality analysis, sentiment analysis, and more. Let's go through the script and provide some documentation for the different components:

- devNetwork(argv) Function:

This function is the entry point of the script. It takes command-line arguments argv and performs various analyses on the repository based on the provided arguments.
The main steps performed by the function are as follows:

    - It checks the Python environment and the installed modules for proper configuration.
    - It parses the provided command-line arguments to get the configuration for the analysis.
    - It sets up sentiment analysis using the SentiStrength tool.
    - It retrieves the repository reference and handles aliases (if any) for commits.
    - It performs commit analysis, tag analysis, centrality analysis, release analysis, PR analysis, issue analysis, politeness analysis, smell detection, and dev analysis for different batches of commits.
    - It collects the results of community smell detection for each batch in a dictionary result and writes the information to an Excel dataset.

## configuration

1. `class Configuration`:

   - Description: This class represents the configuration settings for the analysis of a GitHub repository.
   - Constructor: Initializes the configuration with the provided parameters.
   - Attributes:
     - `repositoryUrl`: The URL of the GitHub repository to be analyzed.
     - `batchMonths`: The number of months to analyze per batch (used for dev network analysis).
     - `outputPath`: The local directory path for storing analysis output.
     - `sentiStrengthPath`: The local directory path to the SentiStrength tool, used for sentiment analysis.
     - `maxDistance`: The string distance metric for calculating similarity.
     - `pat`: The GitHub PAT (personal access token) used for querying the GitHub API.
     - `googleKey`: The Google Cloud API Key used for authentication with the Perspective API (optional).
     - `startDate`: The start date of the project life (optional).
   - Note: The class also derives `repositoryOwner` and `repositoryName` from the `repositoryUrl`, and it constructs the `repositoryPath`, `resultsPath`, and `metricsPath` attributes based on other parameters.

2. `def parseAliasArgs(args: Sequence[str])`:

   - Description: Parses the command-line arguments for alias extraction from GitHub repositories.
   - Parameters: `args` - A sequence of command-line arguments passed to the script.
   - Returns: A `Configuration` object containing the parsed configuration settings.
   - Note: This function defines an argument parser to extract the required command-line arguments for alias extraction. It performs basic validations for the provided arguments, such as checking for valid repository URLs and required PATs.

3. `def parseDevNetworkArgs(args: Sequence[str])`:
   - Description: Parses the command-line arguments for network and statistical analysis on GitHub repositories.
   - Parameters: `args` - A sequence of command-line arguments passed to the script.
   - Returns: A `Configuration` object containing the parsed configuration settings.
   - Note: This function defines an argument parser to extract the required command-line arguments for dev network analysis. It performs basic validations for the provided arguments, such as checking for valid repository URLs, required PATs, and the existence of necessary SentiStrength files.

The `Configuration` class and the `parseAliasArgs()` and `parseDevNetworkArgs()` functions work together to parse and validate the command-line arguments and store them in a convenient configuration object for later use during the analysis of the GitHub repositories.

The script seems to have specific requirements for the arguments it expects, such as the presence of a valid GitHub repository URL, a GitHub PAT for querying the API, and a local directory path for various tools and analysis output. It also performs checks to ensure that the required SentiStrength files are available in the specified path.

# repoLoader

1. `def getRepo(config: Configuration)`:

   - Description: This function is responsible for obtaining a reference to the Git repository for analysis.
   - Parameters:
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns: A GitPython `Repo` object representing the repository reference.
   - Note: This function checks if the local repository already exists in the specified `repositoryPath`. If the repository doesn't exist, it will clone the repository from the provided `repositoryUrl` using the GitPython library. If the repository already exists, it opens the repository from the local path.

2. `class Progress(git.remote.RemoteProgress)`:
   - Description: This class is a custom implementation of `git.remote.RemoteProgress`, which is used to monitor the progress of Git operations (e.g., cloning a repository).
   - Method:
     - `update(self, op_code, cur_count, max_count=None, message="")`: This method overrides the `update()` method in the base class `git.remote.RemoteProgress`. It is called to display progress updates during Git operations. In this specific implementation, it prints the current progress line while cloning the repository.

Please note that the provided code assumes the presence of the `Configuration` class from the `configuration.py` file, as it is passed as an argument to the `getRepo()` function. The `Progress` class is used internally by the `getRepo()` function to display progress during the cloning process.

Overall, the `repoLoader.py` file defines the necessary functions to obtain and load the Git repository for further analysis, using the GitPython library.

# commitAnalysis

Sure! Below is the documentation for the functions in the `commitAnalysis.py` file:

1. `def commitAnalysis(senti: PySentiStr, commits: List[git.Commit], delta: relativedelta, config: Configuration)`:

   - Description: This function performs commit analysis on a list of Git commits for a given repository.
   - Parameters:
     - `senti`: An instance of the `PySentiStr` class used for sentiment analysis on commit messages.
     - `commits`: A list of `git.Commit` objects representing the commits to analyze.
     - `delta`: A `relativedelta` object representing the time duration for each batch.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns:
     - `batchDates`: A list of dates representing the start date of each batch analyzed.
     - `authorInfoDict`: A dictionary containing commit analysis information for each author.
     - `daysActive`: A list containing the number of active days for each batch analyzed.
   - Note: This function processes the commits, splits them into batches based on the `delta`, and runs commit analysis for each batch using the `commitBatchAnalysis()` function.

2. `def commitBatchAnalysis(idx: int, senti: PySentiStr, commits: List[git.Commit], config: Configuration)`:
   - Description: This function performs commit analysis on a batch of Git commits.
   - Parameters:
     - `idx`: An integer representing the index of the batch being analyzed.
     - `senti`: An instance of the `PySentiStr` class used for sentiment analysis on commit messages.
     - `commits`: A list of `git.Commit` objects representing the commits in the batch.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns:
     - `authorInfoDict`: A dictionary containing commit analysis information for each author in the batch.
     - `daysActive`: The number of active days for the batch.
   - Note: This function iterates through the commits in the batch, extracts commit information, and performs commit analysis, including sentiment analysis on commit messages and calculating active days for authors.

Please note that some parts of the code are specific to the project's analysis requirements, such as outputting CSV files and calculating various statistics. The code also uses external libraries like `Bar` from `progress.bar` for displaying progress during the analysis and `PySentiStr` for sentiment analysis on commit messages. The actual functionality and output might depend on the specific configuration and data being used during the analysis.

# centralityAnalisys

Centrality analysis is a network analysis technique used to identify and measure the importance or prominence of nodes (vertices) within a network. In the context of social networks, a node typically represents an individual, and centrality analysis helps to determine the significance or influence of individuals based on their relationships and interactions with other nodes in the network.

In the provided code, centrality analysis is applied to version control repositories, specifically Git repositories. The goal of the centrality analysis is to identify and measure the importance or prominence of individual developers (authors) based on their interactions and contributions to the repository.

The code is divided into two main functions, `centralityAnalysis()` and `processBatch()`, which collectively perform centrality analysis on the Git repository.

1. `centralityAnalysis()` function:

   - This function takes a list of commits, a time interval (delta), a list of batch dates, and a configuration object (`Configuration`) as input.
   - The `centralityAnalysis()` function works in batches, dividing the commits into smaller time intervals represented by `batchDates`.
   - For each batch, the function calls the `processBatch()` function to analyze the interactions between authors in that batch.
   - The function returns a list of core developers for each batch, where core developers are those with high centrality within that batch.

2. `processBatch()` function:
   - This function takes a batch of commits, a batch index, and the configuration object as input.
   - It performs the actual centrality analysis for a given batch of commits.
   - The function iterates through the commits and extracts the authors' information for each commit.
   - For each author, it identifies other authors who have committed code within a specific time window (1 month before and 1 month after the author's commit). These related authors are considered to have interactions with the main author.
   - The function constructs a graph using NetworkX to represent the interactions between authors, where nodes represent authors and edges represent interactions.
   - The centrality measures, including closeness centrality, betweenness centrality, and degree centrality, are computed for each author using NetworkX functions.
   - The function also calculates the network density, which is the ratio of the number of edges to the maximum possible number of edges in the graph.
   - Additionally, the function identifies communities within the graph using the greedy modularity community detection algorithm.
   - The results of the centrality analysis and community detection are saved into CSV files and other tabular data for further analysis.

In summary, the `centralityAnalysis()` function divides the repository commits into batches, and for each batch, the `processBatch()` function performs centrality analysis on the interactions between authors. The results include centrality measures and community information, providing insights into the importance and influence of individual developers and the overall structure of interactions within the Git repository.

1. `def centralityAnalysis(commits: List[Commit], delta: relativedelta, batchDates: List[datetime], config: Configuration)`:

   - Description: This function performs centrality analysis on a list of Git commits using the NetworkX library to create a graph representing author relationships based on related commits.
   - Parameters:
     - `commits`: A list of `git.Commit` objects representing the commits to analyze.
     - `delta`: A `relativedelta` object representing the time duration for each batch.
     - `batchDates`: A list of dates representing the start date of each batch analyzed.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns:
     - `coreDevs`: A list containing high centrality authors for each batch of commits analyzed.
   - Note: This function processes the commits in batches, calculates the author relationships, and performs centrality analysis on the author network using the `prepareGraph()` function.

2. `def processBatch(batchIdx: int, commits: List[Commit], config: Configuration)`:

   - Description: This function processes a batch of Git commits and calculates the author relationships for centrality analysis.
   - Parameters:
     - `batchIdx`: An integer representing the index of the batch being analyzed.
     - `commits`: A list of `git.Commit` objects representing the commits in the batch.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns:
     - `batchCoreDevs`: A list containing high centrality authors for the current batch.
   - Note: This function iterates through the commits in the batch, calculates related authors, and prepares the data for centrality analysis.

3. `def buildGraphQlNetwork(batchIdx: int, batch: list, prefix: str, config: Configuration)`:

   - Description: This function builds a graph representing author relationships for centrality analysis using data from a batch of commits.
   - Parameters:
     - `batchIdx`: An integer representing the index of the batch being analyzed.
     - `batch`: A list containing lists of authors for each batch.
     - `prefix`: A prefix to be used for the output files.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Note: This function is not used in the current code and may not be needed for the central analysis process.

4. `def prepareGraph(allRelatedAuthors: dict, authorItems: Counter, batchIdx: int, outputPrefix: str, config: Configuration)`:

   - Description: This function prepares the author network graph, performs centrality analysis, and outputs the results.
   - Parameters:
     - `allRelatedAuthors`: A dictionary containing authors as keys and sets of related authors as values.
     - `authorItems`: A Counter object representing the count of commits for each author.
     - `batchIdx`: An integer representing the index of the batch being analyzed.
     - `outputPrefix`: A prefix to be used for the output files.
     - `config`: An instance of the `Configuration` class containing the configuration settings for the analysis.
   - Returns:
     - `highCentralityAuthors`: A list containing high centrality authors for the current batch.
   - Note: This function builds the NetworkX graph, performs centrality analysis using various metrics, outputs the results to CSV files, and generates a visual representation of the author network using matplotlib.

5. `def findRelatedCommits(author, earliestDate, latestDate, commit)`:
   - Description: This function checks if a commit is related to a specific author based on the author's name and commit date.
   - Parameters:
     - `author`: The name of the author.
     - `earliestDate`: The earliest date to consider for related commits.
     - `latestDate`: The latest date to consider for related commits.
     - `commit`: A `git.Commit` object representing the commit to check.
   - Returns:
     - `isInRange`: A boolean indicating whether the commit is related to the specified author and within the specified date range.
   - Note: This function is a helper function used in the `processBatch()` function to identify related commits.

# tagAnalysis

The `tagAnalysis.py` script is aimed at performing analysis on tags in a Git repository. Tags in Git are used to mark specific points in the version history, often representing release points or important milestones in the development process. The script aims to analyze the tags and provide insights into the distribution and activity of tags over time.

The script consists of three main functions: `tagAnalysis()`, `outputTags()`, and two helper functions `getTaggedDate()` and `formatDate()`.

1. `tagAnalysis()` function:

   - This function takes a Git repository (`git.Repo`), a time interval (`delta`), a list of batch dates (`batchDates`), a list of days active for each batch (`daysActive`), and a configuration object (`Configuration`) as input.
   - It first sorts the repository tags based on their tagged dates using the `getTaggedDate()` function.
   - It then divides the tags into batches based on the batch dates provided and calls the `outputTags()` function to analyze and output information for each batch.

2. `outputTags()` function:

   - This function takes the batch index (`idx`), a list of tag information (`tagInfo`), the number of days active in the batch (`daysActive`), and the configuration object (`Configuration`) as input.
   - The function calculates the Frequency of New tags (FN) by dividing the number of tags in the batch by the number of days active in that batch.
   - It outputs the FN value and the total number of tags in the batch to the results CSV file.
   - It also outputs detailed tag information, including tag path, tagged date, and the number of commits in each tag, to a separate CSV file.

3. `getTaggedDate()` function:

   - This is a helper function that takes a Git tag object and returns the tagged date.
   - If the tag is an annotated tag, it retrieves the tagged date from the tag object's timestamp.
   - If the tag is a lightweight tag (i.e., a reference to a commit), it retrieves the tagged date from the commit's committed datetime.

4. `formatDate()` function:
   - This is a helper function that takes a datetime object and returns its string representation in the format "YYYY-MM-DD".

In summary, the script conducts an analysis of Git repository tags in batches based on specified time intervals. It calculates the Frequency of New tags (FN) for each batch, which represents the average number of new tags created per day during that time period. It also provides detailed information about each tag, including its path, tagged date, and the number of commits associated with it. The script is useful for understanding how tags are distributed over time and gaining insights into the development history of the Git repository.
