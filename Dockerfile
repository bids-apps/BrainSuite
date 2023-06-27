FROM yeunkim/bidsapphead:2023

ENV BrainSuiteVersion="23a"

RUN wget --no-check-certificate https://brainsuite.org/data/BIDS/BrainSuite23a_BIDS.tgz && tar xzvf BrainSuite23a_BIDS.tgz -C /opt/ && \
    rm BrainSuite23a_BIDS.tgz 
RUN Rscript -e 'install.packages("/opt/BrainSuite23a/bstr/bstr_0.4.tar.gz", repos = NULL,  type = "source")'


ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd / && wget -qO- https://github.com/ajoshiusc/bfp/releases/download/bfp_ver23a1_Matlab2019b_release/bfp_ver23a1_Matlab2019b_release.tar.gz | tar xvz
RUN mv /bfp_ver23a1_Matlab2019b_release /bfp
RUN mv /bfp/bfp_source/* /bfp && mv /bfp/bfp_binaries/* /bfp/ && rm -r bfp/bfp_binaries /bfp/bfp_source
ENV BFP=/bfp
ENV PATH="${BFP}:$PATH"

# RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/BrainSuite23a_beta_bin.tar.gz && \
#     tar xvzf BrainSuite23a_beta_bin.tar.gz -C /opt/BrainSuite${BrainSuiteVersion}/bin/
# RUN wget -O /opt/BrainSuite${BrainSuiteVersion}/bin/gsmooth http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/gsmooth22a_x86_64-pc-linux-gnu 
# RUN cd / && wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bdp_23aMaskOnly_build0084_linux.tar.gz && \
#     tar xzf bdp_23aMaskOnly_build0084_linux.tar.gz && mv bdp_23aMaskOnly_build0084_linux/* /opt/BrainSuite${BrainSuiteVersion}/bdp/
# RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/setup_bstr23a.py && python setup_bstr23a.py

COPY QC/qcState.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
COPY QC/makeMask.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
RUN cd opt/BrainSuite${BrainSuiteVersion}/bin/  && chmod ugo+rx qcState.sh makeMask.sh

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/
COPY fsl/epi.py /nipype/nipype/interfaces/fsl/
COPY fsl/quad_mot.py /usr/local/miniconda/lib/python3.7/site-packages/eddy_qc/QUAD/quad_mot.py
COPY fsl/quad.py /usr/local/miniconda/lib/python3.7/site-packages/eddy_qc/QUAD/quad.py
RUN sed -i 's/EpiReg/EpiReg, EddyQuad/' /nipype/nipype/interfaces/fsl/__init__.py

SHELL ["/bin/bash", "-c"]
RUN source /usr/share/fsl/5.0/etc/fslconf/fsl.sh

COPY ./bfp_sample_config_preproc.ini /config.ini
COPY ./bfp_sample_config_stats.ini /bfp_config_stats.ini

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

