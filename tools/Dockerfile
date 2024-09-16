# docker file for assets bulid
# see ./tools

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND noninteractive

RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update 

RUN \  
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common && \
  apt-get install -y curl git man unzip wget 

RUN apt-get install -y fish

RUN apt-get install -y  \
        apt-transport-https \
        build-essential \
        ca-certificates \
        curl \
        git \
        libssl-dev \
        wget 


RUN mkdir -p /usr/local/nvm
ENV NVM_DIR /usr/local/nvm 
ENV NODE_VERSION 10

# Install nvm with node and npm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
RUN . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/v$NODE_VERSION/bin:$PATH

RUN apt-get install -y libjpeg-dev
RUN apt-get install -y optipng
RUN apt-get install -y jpegoptim pngquant


ENV PYTHON_VERSION=2.7.18

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    curl \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    libbz2-dev \
    tk-dev


RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz && \
    tar -xvzf Python-${PYTHON_VERSION}.tgz && \
    cd Python-${PYTHON_VERSION} && \
    ./configure --enable-optimizations && \
    make -j5 && \
    make install

RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py && \
    python2 get-pip.py && \
    rm get-pip.py

RUN python2 --version && pip2 --version

RUN apt install -y autoconf tree

# Set environment variables.
ENV HOME /root

# Define working directory.
WORKDIR /root

# Define default command.
CMD ["fish"]