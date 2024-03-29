FROM docker.io/python:3.10.2-bullseye

USER root

COPY ./fakepred /opt/fakepred
RUN chmod 777 /opt/fakepred

RUN rm -rf /opt/fakepred/predicter/

# https://gist.github.com/varyonic/dea40abcf3dd891d204ef235c6e8dd79
RUN apt-get update -y

# We need wget to set up the PPA and xvfb to have a virtual screen and unzip to install the Chromedriver
RUN apt-get install -y wget xvfb unzip


#Upgrade pip
RUN pip3 install --no-cache-dir -U pip

RUN pip3 install --no-cache-dir -U setuptools

COPY requirements-celery-scrapper.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN apt-get install xvfb

COPY ./docker/celery-scrapper/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1


# # Set up the Chrome PPA
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
# RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# # Update the package list and install chrome
# RUN apt-get update -y
# RUN apt-get install -y google-chrome-stable

# # Set up Chromedriver Environment variables
# ENV CHROMEDRIVER_VERSION 98.0.4758.102
# ENV CHROMEDRIVER_DIR /chromedriver
# RUN mkdir $CHROMEDRIVER_DIR

# # Download and install Chromedriver
# RUN wget -q --continue -P $CHROMEDRIVER_DIR "http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
# RUN unzip $CHROMEDRIVER_DIR/chromedriver* -d $CHROMEDRIVER_DIR

# # Put Chromedriver into the PATH
# ENV PATH $CHROMEDRIVER_DIR:$PATH

# EXPOSE 4444

# https://nander.cc/using-selenium-within-a-docker-container
# Adding trusting keys to apt for repositories
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adding Google Chrome to the repositories
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Updating apt to see and install Google Chrome
RUN apt-get -y update

# Magic happens
RUN apt-get install -y google-chrome-stable

# Installing Unzip
RUN apt-get install -yqq unzip

# Download the Chrome Driver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip

# Unzip the Chrome Driver into /usr/local/bin directory
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

RUN chmod 777 /root/

# Set display port as an environment variable
ENV DISPLAY=:99

ENTRYPOINT ["/opt/docker-entrypoint.sh"]
