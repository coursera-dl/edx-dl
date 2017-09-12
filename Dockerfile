FROM python:3.4-slim

LABEL maintainer "opsxcq@strm.sh"

WORKDIR /src
COPY requirements.txt /src
RUN pip install -r requirements.txt

COPY requirements-dev.txt /src
RUN pip install -r requirements-dev.txt

COPY . /src
RUN python setup.py install

WORKDIR /
VOLUME /Downloaded
ENTRYPOINT ["edx-dl"]
CMD ["--help"]
