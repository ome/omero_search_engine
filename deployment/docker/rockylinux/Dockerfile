#docker build . -t searchengine
# docker build . -f deployment/docker/rockylinux/Dockerfile -t searchengine
FROM rockylinux/rockylinux:9.0
USER root
RUN dnf update -y
RUN dnf groupinstall "Development Tools" -y
RUN  dnf install libpq-devel -y
RUN dnf install python3-pip -y
RUN dnf install "python3.12-devel.x86_64" -y
RUN dnf install  python3.12  -y
RUN dnf install -y  python3.12-pip -y
RUN dnf clean all && rm -rf /var/cache/yum
RUN mkdir /searchengine
ADD .  /searchengine
ADD  deployment/docker/rockylinux/start_gunicorn_search_engine.sh /searchengine
ADD  deployment/docker/rockylinux/run_app.sh /searchengine
ADD  deployment/docker/rockylinux/run_celery.sh /searchengine
ADD  deployment/docker/rockylinux/run_celery_beat.sh /searchengine
RUN cd /searchengine
RUN mkdir /etc/searchengine
RUN mkdir /etc/searchengine/chachedata
RUN mkdir /etc/searchengine/logs
RUN python3.12 -m pip install "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"
RUN python3.12 -m pip install --upgrade "certifi>=2026.10.19"
WORKDIR /searchengine
RUN python3.12 -m pip install -r  requirements.txt
RUN python3.12 -m pip install gunicorn
EXPOSE 5577
ENTRYPOINT ["bash", "run_app.sh"]
