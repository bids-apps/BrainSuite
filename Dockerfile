FROM yeunkim/brainsuitebidsapp:stable

ENV BrainSuiteVersion="21a"

COPY QC/qcState.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
COPY QC/makeMask.sh /opt/BrainSuite${BrainSuiteVersion}/bin/
RUN cd opt/BrainSuite${BrainSuiteVersion}/bin/  && chmod ugo+rx qcState.sh makeMask.sh

COPY brainsuite/brainsuite.py /nipype/nipype/interfaces/brainsuite/
COPY brainsuite/__init__.py /nipype/nipype/interfaces/brainsuite/

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

