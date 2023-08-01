FROM ubuntu:20.04 

WORKDIR /app

COPY . .
COPY setup.sh .

RUN apt-get update && apt-get install --no-install-recommends -y wget python3.8 python3.8-venv python3-pip build-essential git && apt-get clean 

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get -y install default-jre-headless openjdk-8-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

RUN ./setup.sh

CMD ["python3", "webService/csDetectorWebService.py"]

EXPOSE 5001

