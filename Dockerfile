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
    wget -q http://ssd.mathworks.com/supportfiles/downloads/R2019b/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    unzip -q MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && \
    ./install -agreeToLicense yes -mode silent && \
    cd / && \
    rm -rf mcr_install

RUN apt-get update # && apt-get install -y --no-install-recommends python-six python-nibabel python-setuptools && \
RUN pip install -Iv https://pypi.python.org/packages/b3/b2/238e2590826bfdd113244a40d9d3eb26918bd798fc187e2360a8367068db/six-1.10.0.tar.gz#md5=34eed507548117b2ab523ab14b2f8b55 && \
    pip install -Iv https://pypi.python.org/packages/e0/ec/c4d49fb2aecb80d1c61f89542fdc0ba9686b232bc24f490caeba69d231b6/nibabel-2.1.0.tar.gz#md5=b5ffc03962aa4875b1ce7cb597730772 && \
    pip install -Iv https://pypi.python.org/packages/87/ba/54197971d107bc06f5f3fbdc0d728a7ae0b10cafca46acfddba65a0899d8/setuptools-27.2.0.tar.gz#md5=b39715612fdc0372dbfd7b3fcf5d4fe5 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
#RUN pip install git+https://github.com/INCF/pybids.git
#RUN pip install git+https://github.com/bids-standard/pybids.git
RUN pip install pybids==0.5.1
RUN pip install grabbit==0.1.2
RUN conda install -y -c anaconda statsmodels
ENV PYTHONPATH=""

# Nipype
RUN git clone https://github.com/nipy/nipype && \
    cd nipype && \
    git checkout bdb7afc && \
    pip install -r requirements.txt && \
    python setup.py develop

# BrainSuite
ENV BrainSuiteVersion=19a
RUN wget -q http://users.bmap.ucla.edu/~yeunkim/BFP/BrainSuite${BrainSuiteVersion}.tar.gz && \
    tar -xzf /BrainSuite${BrainSuiteVersion}.tar.gz && \
    mv /BrainSuite${BrainSuiteVersion} /opt && \
    cd /opt/BrainSuite${BrainSuiteVersion}/bin && \
    chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion} && \
    cd / && \
    rm BrainSuite${BrainSuiteVersion}.tar.gz

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}


## Install the validator
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_6.x | bash - && \
    apt-get remove -y curl && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN npm install -g bids-validator@0.19.2

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}





RUN apt-get update && apt-get install -y --no-install-recommends gfortran
RUN apt-get install -y pandoc
#RUN conda install -y -c r r-base


#RUN apt-get install -y dbus && dbus-uuidgen > /opt/conda/var/lib/dbus/machine-id.mzEonjpe
#RUN  apt-get update &&  apt-get clean &&  apt-get autoremove &&  apt-get update && apt-get upgrade -y && \
#    dpkg --configure -a && apt-get install -y -f
#RUN apt-get install -y aptitude && aptitude install -f
RUN install -d /opt/conda/var/lib/dbus/
RUN apt-get install -y dbus && dbus-uuidgen > /opt/conda/var/lib/dbus/machine-id
RUN echo "deb http://cran.rstudio.com/bin/linux/ubuntu xenial/" |  tee -a /etc/apt/sources.list && \
    gpg --keyserver keyserver.ubuntu.com --recv-key E084DAB9 && gpg -a --export E084DAB9 | apt-key add - && \
    apt-get update && apt-get install -y --allow-unauthenticated r-base

#RUN wget https://pypi.python.org/packages/75/a4/182f9dc82934768680b663968115cc3e7e4a1be24478cbb2e1ed44e22b60/rpy2-2.4.0.tar.gz && \
#    tar -xvf rpy2-2.4.0.tar.gz && \
#    cd rpy2-2.4.0 && python setup.py install

## install FSL
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sSL http://neuro.debian.net/lists/xenial.us-ca.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    wget -q -O- http://neuro.debian.net/_static/neuro.debian.net.asc | apt-key add - && \
    apt-get update && \
    apt-get remove -y curl && \
    apt-get install -y --no-install-recommends fsl-core=5.0.9-5~nd16.04+1 && \
    apt-get install -y --no-install-recommends afni=16.2.07~dfsg.1-5~nd16.04+1 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN cd / && wget -qO- http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bfp_ver2p28.tar.gz | tar xvz
# RUN rm /bfp_ver2p24.tar.gz
RUN mv bfp_ver2p28 bfp
ENV BFP=/bfp
ENV PATH="${BFP}:$PATH"

ENV INIFile=/config.ini
#RUN echo [main] >> $INIFile && \
RUN echo AFNIPATH=/usr/lib/afni >> $INIFile && \
    echo BFPPATH=${BFP} >> $INIFile && \
    echo BrainSuitePath=/opt/BrainSuite${BrainSuiteVersion} >> $INIFile && \
    echo LD_LIBRARY_PATH=/usr/lib/fsl/5.0 >> $INIFile && \
    echo CONTINUERUN=1 >> $INIFile && \
    echo MultiThreading=1 >> $INIFile && \
    echo EnabletNLMPdfFiltering=1 >> $INIFile && \
    echo fpr=0.001 >> $INIFile && \
    echo FSLOUTPUTTYPE=NIFTI_GZ >> $INIFile && \
    echo FSLPATH=/usr/share/fsl/5.0 >> $INIFile && \
    echo FWHM=6 >> $INIFile && \
    echo HIGHPASS=0.005 >> $INIFile && \
    echo LOWPASS=0.1 >> $INIFile && \
    echo memory=16 >> $INIFile && \
    echo scbPath=/bfp/SCB.mat >> $INIFile && \
    echo EnableShapeMeasures=0 >> $INIFile && \
    echo T1SpaceProcessing=1 >> $INIFile && \
    echo FSLRigid=0 >> $INIFile && \
    echo T1mask=1 >> $INIFile && \
    echo SimRef=1 >> $INIFile && \
    echo RunDetrend=1 >> $INIFile && \
    echo RunNSR=1 >> $INIFile


RUN apt-get update && apt-get -y install build-essential imagemagick

RUN apt-get update && apt-get -y install vim

RUN conda install -y -c r rpy2
RUN conda install libgcc
RUN conda install -y -c conda-forge tqdm nilearn

RUN cd / && wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bssr_0.2.1.RC.tar.gz

RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/install_dep.py && \
    python install_dep.py

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/
#COPY bfp/supp_data/* /bfp_ver2p19/supp_data/
RUN cd /usr/share/fsl/5.0/data/ && install -d standard
COPY bfp/standard/MNI152_T1_2mm.nii.gz /usr/share/fsl/5.0/data/standard/

COPY . /BrainSuite
#RUN bash /BrainSuite/R/installR.sh
RUN chmod +x /BrainSuite/run.py


ENTRYPOINT ["/BrainSuite/run.py"]

