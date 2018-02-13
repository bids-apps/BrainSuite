FROM ubuntu:16.04
RUN apt-get -y update --fix-missing && apt-get install -y \
    build-essential \
    git \
    libxt6 \
    unzip \
    wget

# Anaconda
RUN mkdir conda_install && cd conda_install && \
    wget -q https://repo.continuum.io/archive/Anaconda2-4.4.0-Linux-x86_64.sh && \
    bash Anaconda2-4.4.0-Linux-x86_64.sh -b -p /opt/conda && \
    cd / && \
    rm -rf conda_install && \
    echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh
ENV PATH /opt/conda/bin:$PATH

# MATLAB MCR
RUN mkdir mcr_install && \
    cd mcr_install && \
    wget -q https://www.mathworks.com/supportfiles/downloads/R2015b/deployment_files/R2015b/installers/glnxa64/MCR_R2015b_glnxa64_installer.zip && \ 
    unzip -q MCR_R2015b_glnxa64_installer.zip && \
    ./install -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr_install

RUN apt-get update && apt-get install -y --no-install-recommends python-six python-nibabel python-setuptools && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN pip install git+https://github.com/INCF/pybids.git
ENV PYTHONPATH=""

# Nipype
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    pip install -r requirements.txt && \
    python setup.py develop

# BrainSuite
RUN wget -q users.bmap.ucla.edu/~yeunkim/private/BrainSuite17a.linux.tgz && \
    tar -xf BrainSuite17a.linux.tgz && \
    mv /BrainSuite17a /opt && \
    cd /opt/BrainSuite17a/bin && \
    chmod -R ugo+r /opt/BrainSuite17a && \
    cd / && \
    rm BrainSuite17a.linux.tgz

RUN chmod -R ugo+r /opt/BrainSuite17a


## Install the validator
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
    apt-get remove -y curl && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN npm install -g bids-validator@0.19.2

ENV PATH=/opt/BrainSuite17a/bin/:/opt/BrainSuite17a/svreg/bin/:/opt/BrainSuite17a/bdp/:${PATH}

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/

ADD . /BrainSuite

RUN apt-get update && apt-get install -y --no-install-recommends gfortran
#RUN apt-get install -y r-cran-rcpp
#RUN conda install -y -c r r-base

RUN  apt-get update &&  apt-get clean &&  apt-get autoremove &&  apt-get update && apt-get upgrade -y && \
    dpkg --configure -a && apt-get install -y -f &&
RUN sudo echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" |  tee -a /etc/apt/sources.list && \
    gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && gpg -a --export E084DAB9 | apt-key add - && \
    apt-get update && apt-get install -y r-base

RUN bash /BrainSuite/R/installR.sh
#RUN wget https://pypi.python.org/packages/75/a4/182f9dc82934768680b663968115cc3e7e4a1be24478cbb2e1ed44e22b60/rpy2-2.4.0.tar.gz && \
#    tar -xvf rpy2-2.4.0.tar.gz && \
#    cd rpy2-2.4.0 && python setup.py install

RUN conda install -y -c r rpy2
RUN conda install libgcc
RUN chmod +x /BrainSuite/run.py

ENTRYPOINT ["/BrainSuite/run.py"]

