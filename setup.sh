#!/bin/bash
# This script prepare the project for use.
# it downloads external resources and create
# the folders that is going to be used by the tool.

# create folders to posterior use
mkdir -p senti
mkdir -p out
mkdir -p logs

# Function to check if a command is available
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if unzip is already installed
if command_exists unzip; then
  echo "unzip is already installed."
else
  # Check if the package manager (apt) is available
  if command_exists apt; then
    # Update package lists
    apt-get update -y

    # Install unzip using apt
    apt-get install -y unzip

    # Check if installation was successful
    if [ $? -eq 0 ]; then
      echo "unzip has been installed successfully."
    else
      echo "Failed to install unzip."
      exit 1
    fi
  else
    echo "Package manager apt is not available. Please install unzip manually."
    exit 1
  fi
fi

# download resources
wget http://sentistrength.wlv.ac.uk/jkpop/SentiStrength.jar -P ./senti
wget http://sentistrength.wlv.ac.uk/jkpop/SentiStrength_Data.zip -P ./senti

# extract to folder
unzip ./senti/SentiStrength_Data.zip -d ./senti/SentiStrength_Data

if command_exists java; then
  echo "java has already been installed"
else
  apt-get install -y openjdk-8-jdk
fi

#convokit
python3 -m spacy download en_core_web_sm

