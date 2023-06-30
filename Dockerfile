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
ENV PATH=${BFP}:${PATH}

COPY nipype/brainsuite/brainsuite.py nipype/brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/
COPY nipype/fsl/epi.py /nipype/nipype/interfaces/fsl/
COPY nipype/fsl/quad_mot.py nipype/fsl/quad.py /usr/local/miniconda/lib/python3.7/site-packages/eddy_qc/QUAD/
RUN sed -i 's/EpiReg/EpiReg, EddyQuad/' /nipype/nipype/interfaces/fsl/__init__.py

COPY ./bfp_sample_config_preproc.ini /config.ini
COPY ./bfp_sample_config_stats.ini /bfp_config_stats.ini

COPY . /BrainSuite
RUN chmod -R ugo+rx /BrainSuite/QC/ /opt/BrainSuite${BrainSuiteVersion}/svreg/bin/ /opt/BrainSuite${BrainSuiteVersion}/bin/ /opt/BrainSuite${BrainSuiteVersion}/bdp/ /bfp/
RUN chmod ugo+rx /BrainSuite/run.py
ENV PATH=/BrainSuite/QC/:${PATH}

ENV FSLDIR=/usr/share/fsl/5.0
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=/usr/lib/fsl/5.0:${PATH}
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

ENTRYPOINT ["/BrainSuite/run.py"]

