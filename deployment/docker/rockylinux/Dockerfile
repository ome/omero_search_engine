#docker build . -t searchengine
# docker build . -f deployment/docker/rockylinux/Dockerfile -t searchengine
FROM rockylinux/rockylinux:9.0
USER root
RUN dnf update -y
RUN dnf install epel-release -y
RUN dnf install  bzip2-devel -y
RUN dnf install wget -y
RUN dnf groupinstall "Development Tools" -y
RUN  dnf install openssl-devel -y
RUN dnf install libffi-devel -y
RUN  dnf install libpq-devel -y
RUN dnf install python3-pip -y
RUN dnf install -y   python3-devel.x86_64
RUN dnf clean all && rm -rf /var/cache/yum
RUN mkdir /searchengine
ADD  deployment/docker/rockylinux/start_gunicorn_serch_engine.sh /searchengine
ADD  deployment/docker/rockylinux/run_app.sh /searchengine
ADD .  /searchengine
RUN cd /searchengine
RUN mkdir /etc/searchengine
RUN mkdir /etc/searchengine/chachedata
RUN mkdir /etc/searchengine/logs
WORKDIR /searchengine
RUN pip3 install -r  requirements.txt
RUN pip3 install gunicorn
EXPOSE 5577
ENTRYPOINT ["bash", "run_app.sh"]
