FROM ubuntu:20.04 

WORKDIR /app

COPY . .
COPY setup.sh .

RUN apt-get update && apt-get install --no-install-recommends -y python3.8 python3.8-venv python3-pip build-essential git && apt-get clean 

RUN pip install -r requirements.txt

RUN ./setup.sh

CMD ["python3", "webService/csDetectorWebService.py"]

EXPOSE 5001

