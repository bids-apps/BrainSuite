FROM yeunkim/bidsapphead

ENV BrainSuiteVersion="21a"
RUN wget http://brainsuite.org/data/BIDS/21a/install_dep.py
RUN python install_dep.py

# BrainSuite
RUN wget -q http://brainsuite.org/data/BIDS/BrainSuite21a.BIDS.tgz && \
    tar -xzf /BrainSuite${BrainSuiteVersion}.BIDS.tgz && \
    mv /BrainSuite${BrainSuiteVersion} /opt && \
    cd /opt/BrainSuite${BrainSuiteVersion}/bin && \
    chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion} && \
    cd / && \
    rm BrainSuite${BrainSuiteVersion}.BIDS.tgz

RUN cd / && curl http://brainsuite.org/wp-content/uploads/2022/08/bssr_0.3.3.tar.gz > /bssr_0.3.3.tar.gz && \
    tar xvfz /bssr_0.3.3.tar.gz
RUN wget http://brainsuite.org/data/BIDS/21a/install_bssr.py && python install_bssr.py

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd / && wget -qO- https://github.com/ajoshiusc/bfp/releases/download/ver5p05/bfp_ver5p05_release.tar.gz | tar xvz
RUN mv /bfp_ver5p05_release/* / && tar xvfz bfp_ver5p05.tar.gz && tar xvfz bfp_source.tar.gz 
RUN rm bfp_source.tar.gz bfp_ver5p05.tar.gz
RUN mv /bfp_source /bfp && mv /bfp_ver5p05/* /bfp/
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

