FROM yeunkim/bidsapphead:2023

ENV BrainSuiteVersion="23a"

# pull brainsuite and install bstr
RUN wget --no-check-certificate https://brainsuite.org/data/BIDS/BrainSuite${BrainSuiteVersion}_BIDS.tgz && tar xzvf BrainSuite${BrainSuiteVersion}_BIDS.tgz -C /opt/ && \
    rm BrainSuite${BrainSuiteVersion}_BIDS.tgz
RUN Rscript -e 'install.packages("/opt/BrainSuite23a/bstr/bstr_0.4.1.tar.gz", repos = NULL,  type = "source")'

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

# copy libtiff files and edit LD_LIBRARY_PATH
RUN mkdir /usr/libtiff && cp /usr/lib/x86_64-linux-gnu/libtiff.so* /usr/libtiff/
ENV TIFF_LD_PATH=/usr/libtiff/

ENV BFP=/opt/BrainSuite${BrainSuiteVersion}/bfp
ENV PATH=${BFP}:${PATH}

COPY nipype/brainsuite/brainsuite.py nipype/brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/
COPY nipype/fsl/epi.py /nipype/nipype/interfaces/fsl/
COPY nipype/fsl/quad_mot.py nipype/fsl/quad.py /usr/local/miniconda/lib/python3.7/site-packages/eddy_qc/QUAD/
RUN sed -i 's/EpiReg/EpiReg, EddyQuad/' /nipype/nipype/interfaces/fsl/__init__.py

COPY ./templates/bfp_sample_config_preproc.ini /config.ini
COPY ./templates/bfp_sample_config_stats.ini /bfp_config_stats.ini

COPY . /BrainSuite
RUN chmod -R ugo+rx /BrainSuite/QC/ /opt/BrainSuite${BrainSuiteVersion}/svreg/bin/ /opt/BrainSuite${BrainSuiteVersion}/bin/ /opt/BrainSuite${BrainSuiteVersion}/bdp/ /opt/BrainSuite${BrainSuiteVersion}/bfp/
RUN chmod ugo+rx /BrainSuite/run.py
ENV PATH=/BrainSuite/QC/:${PATH}

ENV FSLDIR=/usr/share/fsl/5.0
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=/usr/share/fsl/5.0/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

ENTRYPOINT ["/BrainSuite/run.py"]
