
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

#TODO: change to miniconda
# Anaconda
#RUN mkdir conda_install && cd conda_install && \
#    wget -q https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh && \
#    bash Anaconda3-2020.02-Linux-x86_64.sh -b -p /opt/conda && \
#    cd / && \
#    rm -rf conda_install && \
#    echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh
#ENV PATH /opt/conda/bin:$PATH

ENV PATH="/usr/local/miniconda/bin:$PATH"
RUN curl -fsSL -o miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py37_4.8.2-Linux-x86_64.sh && \
    bash miniconda.sh -b -p /usr/local/miniconda && \
    rm miniconda.sh && \
    conda config --add channels conda-forge && \
    conda install -y mkl=2020.0 mkl-service=2.3.0 numpy=1.18.1 nibabel=3.0.2 pandas=1.0.3 six=1.14.0 setuptools=45.2.0 && sync && \
    conda clean -tipsy && sync && \
    /usr/local/miniconda/bin/pip install --no-cache-dir pybids==0.6.5 && \
    /usr/local/miniconda/bin/pip install --no-cache-dir grabbit
RUN conda install -y -c anaconda statsmodels

# MATLAB MCR
RUN mkdir mcr_install && \
    cd mcr_install && \
    wget -q http://ssd.mathworks.com/supportfiles/downloads/R2019b/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    unzip -q MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    ./install -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr_install

#RUN apt-get update
#RUN apt-get install -y --no-install-recommends python-six python-nibabel python-setuptools
#RUN pip install pybids==0.6.5
#RUN pip install grabbit #==0.1.2
#RUN conda install -y -c anaconda statsmodels
ENV PYTHONPATH=""

# Nipype
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    git checkout bdb7afc && \
    pip install -r requirements.txt && \
    python setup.py develop

# BrainSuite
ENV BrainSuiteVersion=19b
RUN wget -q http://brainsuite.org/data/BIDS/BrainSuite${BrainSuiteVersion}.BIDS.tgz && \
    tar -xzf /BrainSuite${BrainSuiteVersion}.BIDS.tgz && \
    mv /BrainSuite${BrainSuiteVersion} /opt && \
    cd /opt/BrainSuite${BrainSuiteVersion}/bin && \
    chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion} && \
    cd / && \
    rm BrainSuite${BrainSuiteVersion}.BIDS.tgz

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}


## Install the validator
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get remove -y curl && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN npm install -g bids-validator@1.4.0

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}



RUN apt-get update && apt-get install -y --no-install-recommends gfortran
RUN apt-get install -y pandoc software-properties-common

RUN install -d /opt/conda/var/lib/dbus/
RUN apt-get install -y dbus && dbus-uuidgen > /opt/conda/var/lib/dbus/machine-id
RUN echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" |  tee -a /etc/apt/sources.list && \
    gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && gpg -a --export E084DAB9 | apt-key add - && \
    apt-get update && apt-get install -y --allow-unauthenticated r-base

RUN cd / && wget -qO- http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bfp.tar.gz | tar xvz
RUN cd / && wget -qO- http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bfp_ver2p30.tar.gz | tar xvz
#RUN rm /bfp_ver2p30.tar.gz
RUN rm -rf bfp_ver2p30/supp_data && mv bfp_ver2p30/* bfp
ENV BFP=/bfp
ENV PATH="${BFP}:$PATH"


#ENV INIFile=/config.ini
##RUN echo [main] >> $INIFile && \
#RUN echo AFNIPATH=/usr/lib/afni >> $INIFile && \
#    echo BFPPATH=${BFP} >> $INIFile && \
#    echo BrainSuitePath=/opt/BrainSuite${BrainSuiteVersion} >> $INIFile && \
#    echo LD_LIBRARY_PATH=/usr/lib/fsl/5.0 >> $INIFile && \
#    echo CONTINUERUN=1 >> $INIFile && \
#    echo MultiThreading=1 >> $INIFile && \
#    echo EnabletNLMPdfFiltering=1 >> $INIFile && \
#    echo fpr=0.001 >> $INIFile && \
#    echo FSLOUTPUTTYPE=NIFTI_GZ >> $INIFile && \
#    echo FSLPATH=/usr/share/fsl/5.0 >> $INIFile && \
#    echo FWHM=6 >> $INIFile && \
#    echo HIGHPASS=0.005 >> $INIFile && \
#    echo LOWPASS=0.1 >> $INIFile && \
#    echo memory=16 >> $INIFile && \
#    echo scbPath=/bfp/SCB.mat >> $INIFile && \
#    echo EnableShapeMeasures=0 >> $INIFile && \
#    echo T1SpaceProcessing=1 >> $INIFile && \
#    echo FSLRigid=0 >> $INIFile && \
#    echo T1mask=1 >> $INIFile && \
#    echo SimRef=1 >> $INIFile && \
#    echo RunDetrend=1 >> $INIFile && \
#    echo RunNSR=1 >> $INIFile


RUN conda install -y -c conda-forge rpy2
RUN conda install libgcc
RUN conda install -y -c conda-forge tqdm nilearn

RUN cd / && wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bssr_0.2.2.tar.gz

RUN wget https://cran.r-project.org/src/contrib/Archive/nloptr/nloptr_1.2.1.tar.gz && \
    R CMD INSTALL nloptr_1.2.1.tar.gz && \
    rm nloptr_1.2.1.tar.gz
RUN wget https://cran.r-project.org/src/contrib/Archive/foreign/foreign_0.8-71.tar.gz && \
    R CMD INSTALL foreign_0.8-71.tar.gz && \
    rm foreign_0.8-71.tar.gz

RUN conda install -c r r-stringi
RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/install_dep.py && \
    python install_dep.py

RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/install_bssr.py && \
    python install_bssr.py
RUN rm /bssr_0.2.2.tar.gz

RUN curl -sSL "http://neuro.debian.net/lists/$( lsb_release -c | cut -f2 ).us-ca.full" >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key add /usr/local/etc/neurodebian.gpg && \
    (apt-key adv --refresh-keys --keyserver hkp://ha.pool.sks-keyservers.net 0xA5D32F012649A5A9 || true)

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
                    fsl-core=5.0.9-5~nd16.04+1 \
                    fsl-mni152-templates=5.0.7-2 \
                    afni=16.2.07~dfsg.1-5~nd16.04+1

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/

COPY ./bfp_sample_config_preproc.ini /config.ini
COPY ./bfp_sample_config_stats.ini /bfp_config_stats.ini

#COPY bfp/standard/MNI152_T1_2mm.nii.gz /usr/share/fsl/5.0/data/standard/

COPY . /BrainSuite

RUN chmod +x /BrainSuite/run.py
RUN chmod a+x /bfp/*


ENTRYPOINT ["/BrainSuite/run.py"]

