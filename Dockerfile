FROM yeunkim/brainsuitebidsapp:parent

ENV BrainSuiteVersion="21a"

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd / && wget -qO- https://github.com/ajoshiusc/bfp/releases/download/bfp_ver23a1_Matlab2019b_release/bfp_ver23a1_Matlab2019b_release.tar.gz | tar xvz
RUN mv /bfp_ver23a1_Matlab2019b_release /bfp
RUN mv /bfp/bfp_source/* /bfp && mv /bfp/bfp_binaries/* /bfp/ && rm -r bfp/bfp_binaries /bfp/bfp_source
ENV BFP=/bfp
ENV PATH="${BFP}:$PATH"

RUN apt-get install -y xvfb libosmesa6-dev


RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/BrainSuite23a_beta_bin.tar.gz && \
    tar xvzf BrainSuite23a_beta_bin.tar.gz -C /opt/BrainSuite${BrainSuiteVersion}/bin/
RUN wget -O /opt/BrainSuite${BrainSuiteVersion}/bin/gsmooth http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/gsmooth22a_x86_64-pc-linux-gnu 
RUN cd / && wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bdp_23aMaskOnly_build0084_linux.tar.gz && \
    tar xvzf http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bdp_23aMaskOnly_build0084_linux.tar.gz -C /opt/BrainSuite${BrainSuiteVersion}/bdp/

COPY QC/qcState.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
COPY QC/makeMask.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
RUN cd opt/BrainSuite${BrainSuiteVersion}/bin/  && chmod ugo+rx qcState.sh makeMask.sh

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/
COPY fsl/epi.py /nipype/nipype/interfaces/fsl/

RUN rm -rf /usr/local/MATLAB/
# install MCR 2023a
RUN mkdir mcr_install && \
    cd mcr_install && \
    wget https://ssd.mathworks.com/supportfiles/downloads/R2023a/Release/2/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2023a_Update_2_glnxa64.zip && \
    unzip MATLAB_Runtime_R2023a_Update_2_glnxa64.zip && \
    ./install -agreeToLicense yes && \
    cd / && \
    rm -rf mcr_install

RUN conda install -y -c https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/public/ fsl-eddy
ENV FSLDIR6=/usr/local/miniconda/
ENV FSLOUTPUTTYPE=NIFTI_GZ 
RUN sed -i 's/FSLDIR/FSLDIR6/' ${FSLDIR6}/bin/fslpython 
RUN sed -i 's/FSLDIR/FSLDIR6/' ${FSLDIR6}/bin/eddy 

COPY ./bfp_sample_config_preproc.ini /config.ini
COPY ./bfp_sample_config_stats.ini /bfp_config_stats.ini

RUN chmod -R ugo+rx /jq-linux64

COPY . /BrainSuite
RUN cd /BrainSuite/QC/ && chmod -R ugo+rx *
RUN cd /opt/BrainSuite${BrainSuiteVersion}/svreg/bin/ && chmod -R ugo+rx *
RUN cd /opt/BrainSuite${BrainSuiteVersion}/bin/ && chmod -R ugo+rx *
RUN cd /opt/BrainSuite${BrainSuiteVersion}/bdp/ && chmod -R ugo+rx *

ENV PATH=/BrainSuite/QC/:${PATH}

RUN chmod +x /BrainSuite/run.py
RUN chmod a+x /bfp/*

RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

ENTRYPOINT ["/BrainSuite/run.py"]

