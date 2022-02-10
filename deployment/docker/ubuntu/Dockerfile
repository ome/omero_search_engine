#docker build . -t searchengine
FROM python:3.9.0
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential
RUN apt-get clean
ADD  omero_search_engine  /searchengine
ADD start_gunicorn_serch_engine.sh /searchengine
ADD run_app.sh /searchengine
RUN cd /searchengine
WORKDIR /searchengine
RUN mkdir /etc/searchengine
RUN mkdir /etc/searchengine/logs
RUN mkdir /etc/searchengine/chachedata
RUN ls -l /searchengine
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --upgrade pip setuptools wheel
RUN pip  install -r  requirements.txt
RUN pip install gunicorn
EXPOSE 5569
RUN echo $HOME
ENTRYPOINT ["bash", "run_app.sh"]