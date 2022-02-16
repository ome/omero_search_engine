#docker build . -t searchengine
# docker build . -f deployment/docker/centos/Dockerfile -t searchengine

FROM centos/python-36-centos7
USER root
RUN yum -y install epel-release
RUN yum -y update
RUN yum install  bzip2-devel -y 

#RUN yum groupinstall "Development Tools" -y
#RUN  yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel python-cliff wget git curl -y
RUN wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tgz
RUN tar xvf Python-3.9.0.tgz
RUN cd Python-3.9.0 && ./configure --enable-optimizations &&  make altinstall
RUN yum clean all && rm -rf /var/cache/yum
RUN mkdir /searchengine
ADD  deployment/docker/centos/start_gunicorn_serch_engine.sh /searchengine
ADD  deployment/docker/centos/run_app.sh /searchengine
ADD .  /searchengine
RUN cd /searchengine
RUN mkdir /etc/searchengine
RUN mkdir /etc/searchengine/chachedata
RUN mkdir /etc/searchengine/logs
WORKDIR /searchengine
RUN pip3.9 install -r  requirements.txt
RUN pip3.9 install gunicorn
EXPOSE 5577
ENTRYPOINT ["bash", "run_app.sh"]


 
