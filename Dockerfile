
########################################################################
### Authored by Chris Markiewicz (Github: effigies)
FROM ubuntu:xenial-20200114

# Pre-cache neurodebian key
COPY neurodebian.gpg /usr/local/etc/neurodebian.gpg

# Prepare environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    curl \
                    bzip2 \
                    ca-certificates \
                    xvfb \
                    build-essential \
                    autoconf \
                    libtool \
                    pkg-config \
                    git && \
    curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y --no-install-recommends \
                    nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
########################################################################

# Install latest pandoc
RUN curl -o pandoc-2.2.2.1-1-amd64.deb -sSL "https://github.com/jgm/pandoc/releases/download/2.2.2.1/pandoc-2.2.2.1-1-amd64.deb" && \
    dpkg -i pandoc-2.2.2.1-1-amd64.deb && \
    rm pandoc-2.2.2.1-1-amd64.deb

RUN apt-get -y update --fix-missing && apt-get install -y \
    libxt6 \
    unzip \
    wget \
    imagemagick

ENV PATH="/usr/local/miniconda/bin:$PATH"
RUN curl -fsSL -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.2-Linux-x86_64.sh && \
    bash miniconda.sh -b -p /usr/local/miniconda && \
    rm miniconda.sh && \
    conda config --add channels conda-forge && \
    conda install -y  numpy=1.18.1 nibabel=3.0.2 setuptools=45.2.0 && sync && \
    conda clean -tipsy && sync && \
    /usr/local/miniconda/bin/pip install --no-cache-dir pybids==0.6.5 && \
    /usr/local/miniconda/bin/pip install --no-cache-dir grabbit && \
    /usr/local/miniconda/bin/pip install --no-cache-dir duecredit
RUN conda install -y -c anaconda statsmodels

# MATLAB MCR
RUN mkdir mcr_install && \
    cd mcr_install && \
    wget -q http://ssd.mathworks.com/supportfiles/downloads/R2019b/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    unzip -q MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    ./install -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr_install

ENV PYTHONPATH=""

# Nipype
RUN git config --global core.compression 0
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    git checkout bdb7afc && \
    pip install -r requirements.txt && \
    python setup.py develop

# Neurodebian
RUN curl -sSL "http://neuro.debian.net/lists/$( lsb_release -c | cut -f2 ).us-ca.full" >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key add /usr/local/etc/neurodebian.gpg && \
    (apt-key adv --refresh-keys --keyserver hkp://ha.pool.sks-keyservers.net 0xA5D32F012649A5A9 || true)

# FSL and AFNI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    fsl-core=5.0.9-5~nd16.04+1 \
                    fsl-mni152-templates=5.0.7-2 \
                    afni=16.2.07~dfsg.1-5~nd16.04+1


## Install the validator
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get remove -y curl && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip uninstall -y pandas && \
    pip install pandas==1.1.5
RUN conda install -y -c anaconda basemap
RUN npm install -g bids-validator

RUN apt-get update && apt-get install -y --no-install-recommends gfortran
RUN apt-get install -y pandoc software-properties-common

# Apache
RUN apt-get install -y apache2
RUN cd / && wget https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64

RUN conda install -y -c conda-forge rpy2
RUN conda install libgcc
RUN conda install -y -c conda-forge tqdm nilearn

RUN apt install -y r-base
RUN conda install -y -c r r-stringi r-stringr r-roxygen2 r-systemfonts r-textshaping r-ragg r-pkgdown r-nloptr r-lme4 r-devtools


