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

RUN pip install -Iv https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz#md5=34eed507548117b2ab523ab14b2f8b55 && \
    pip install -Iv https://pypi.python.org/packages/e0/ec/c4d49fb2aecb80d1c61f89542fdc0ba9686b232bc24f490caeba69d231b6/nibabel-2.1.0.tar.gz#md5=b5ffc03962aa4875b1ce7cb597730772 && \
    pip install -Iv https://pypi.python.org/packages/87/ba/54197971d107bc06f5f3fbdc0d728a7ae0b10cafca46acfddba65a0899d8/setuptools-27.2.0.tar.gz#md5=b39715612fdc0372dbfd7b3fcf5d4fe5 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*  
RUN pip install git+https://github.com/INCF/pybids.git
ENV PYTHONPATH=""

# Nipype
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    git checkout bdb7afc && \
    pip install -r requirements.txt && \
    python setup.py develop

# BrainSuite
RUN wget -q users.bmap.ucla.edu/~yeunkim/private/BrainSuite17a.linux.tgz && \
    tar -xf BrainSuite17a.linux.tgz && \
    cd BrainSuite17a/bin && \
    chmod -R ugo+r /BrainSuite17a && \
    cd / && \
    rm BrainSuite17a.linux.tgz

RUN chmod -R ugo+r /BrainSuite17a


## Install the validator
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
    apt-get remove -y curl && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN npm install -g bids-validator@0.19.2

ENV PATH=/BrainSuite17a/bin/:/BrainSuite17a/svreg/bin/:/BrainSuite17a/bdp/:${PATH}

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/

ADD . /qc-system

RUN chmod +x ./qc-system/run.py

ENTRYPOINT ["./qc-system/run.py"]
