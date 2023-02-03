FROM yeunkim/brainsuitebidsapp:parent

ENV BrainSuiteVersion="21a"

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd / && wget -qO- https://github.com/ajoshiusc/bfp/releases/download/ver5p05/bfp_ver5p05_release.tar.gz | tar xvz
RUN mv /bfp_ver5p05_release/* / && tar xvfz bfp_ver5p05.tar.gz && tar xvfz bfp_source.tar.gz
RUN rm bfp_source.tar.gz bfp_ver5p05.tar.gz
RUN mv /bfp_source /bfp && mv /bfp_ver5p05/* /bfp/
RUN wget -qO- https://github.com/ajoshiusc/bfp/releases/download/ver22RC2_Matlab2019b/bfp_ver22RC2_Matlab2019b.tar.gz | tar xvz
RUN rm -r /bfp/supp_data/ && mv /bfp_ver22RC2_Matlab2019b/* /bfp
ENV BFP=/bfp
ENV PATH="${BFP}:$PATH"

RUN apt-get install -y xvfb libosmesa6-dev

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

