# CSDETECTOR Refactoring

In this document, we will address the refactoring of the [CSDETECTOR](https://github.com/Nuri22/csDetector) tool, with the aim of enhancing GitHub data extraction. The current tool has some limitations that affect its efficiency and functionality.

Here we will analyze the tool in a way that allows us to understand its modules independently and facilitate the refactoring process to achieve the goal of improving GitHub data extraction.

## Objectives

Through this refactoring, we have three main objectives to achieve success:

- [x] Accept multiple GitHub tokens.
- [x] Improve maintainability.
- [ ] Handle potential bot-generated comments.

The primary initial objectives of refactoring the [CSDETECTOR](https://github.com/Nuri22/csDetector) tool are as follows:

- **Accept Multiple GitHub Tokens**: The current tool operates with a single GitHub authentication token. However, to enhance data extraction and avoid rate limitations, it is desirable for the tool to be capable of accepting and managing multiple authentication tokens. This will enable a more efficient distribution of requests to the GitHub API.
- **Handle Potential Bot-Generated Comments**: While analyzing repositories on GitHub, it is common to encounter comments made by bots. These comments may contain irrelevant or duplicate information, impacting the quality of the extracted data. The goal is to implement mechanisms that identify and filter out these comments, improving the accuracy and relevance of the obtained results.
- **Improve Maintainability**: The tool's structure and code need to be reorganized and optimized to improve maintainability. This includes clear module division, adherence to programming best practices, removal of redundant code, and proper documentation of the source code. A well-organized tool will be easier to understand, modify, and extend in the future.

### About CSDETECTOR

**Key Modules and Functionalities**

- **Metrics Extraction Module:**
  1. **Developer Artifact Extraction:** Begins by collecting artifacts from the version control system.
  2. **Developer Alias Extraction:** Retrieves aliases (identifiers) of developers.
  3. **Social Graph Construction:** Utilizes aliases to create a social graph interconnecting developers.
  4. **Sentiment-Related Metrics Calculation:** Analyzes content to calculate sentiment metrics.
  5. **Socio-Technical Metrics Calculation:** Uses the social graph to quantify collaboration among developers.

- **Community Smells Detection Module:**
  1. **Community Smells Detection:** Utilizes extracted features and calculated metrics as input.
  2. **Pre-Trained Models:** Employs pre-trained models to identify potential "code smells" in the community.
  
This system operates in two main stages: first, it extracts information related to developers and their interactions from the development community; then, it utilizes this information to detect possible issues or "Community Smells".

# Usage Instructions

Follow these instructions to set up and use the tool effectively.

## Prerequisites

- Python 3.x is installed on your system.
- Git is installed (for repository cloning).
- Google Cloud API Key (if using Perspective API).
- SentiStrength tool is downloaded (See [setup](setup.sh)).

## Setup

1. Clone the CSDETECTOR repository from GitHub:
   
   ```bash
   git clone https://github.com/ViniciusTei/csDetector.git
   cd csDetector
   ```

2. Create and activate a virtual environment (recommended):
   
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required Python packages:
   
   ```bash
   pip install -r requirements.txt
   ```

4. Run the setup script to install additional components:
   
   ```bash
   sh setup.sh
   ```

## Usage

Navigate to the root directory of the CSDETECTOR tool in your terminal before executing the following commands.

```bash
cd /path/to/csDetector
```

Run the main script `main.py` with the required arguments:

```bash
python main.py -p <GitHub_PAT> -r <repository_url> -s <sentiStrength_path> -o <output_path>
```

### Optional Arguments:

- `-g, --googleKey`: Google Cloud API Key for Perspective API authentication.
- `-m, --batchMonths`: Number of months to analyze per batch (default is 9999, i.e., all data).
- `-sd, --startDate`: Start date of the project's life (optional).
- `-d, --debug`: Enable debug logging (optional, only for development).
- `-a, --alias`: Extract authors' aliases for the repository (optional, if it is enabled the tool should take longer to run).

**Example:**

```bash
python main.py -p <GitHub_PAT> -g <Google_API_Key> -r <repository_url> -m 6 -s <sentiStrength_path> -o <output_path> -sd 2020-01-01 -d true -a true
```

## Note

- **GitHub PAT (Personal Access Token)**: Obtain from your GitHub account settings. Multiple tokens can be used for improved data extraction efficiency.
- **Google Cloud API Key**: Required only if using Perspective API.
- **Repository URL**: URL of the GitHub repository you want to analyze.
- **SentiStrength Path**: Path to the SentiStrength tool (default is `senti`).
- **Output Path**: Local directory path for analysis output (default is `out`).

For more details and advanced usage, consult the README in the [CSDETECTOR repository](https://github.com/Nuri22/csDetector).

