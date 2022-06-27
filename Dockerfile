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

RUN cd / && wget http://brainsuite.org/data/BIDS/21a/bssr_0.3.1b.tar.gz && tar xzf bssr_0.3.1b.tar.gz
#RUN cd / && wget http://brainsuite.org/wp-content/uploads/2021/11/bssr_0.3.2.tar.gz
RUN wget http://brainsuite.org/data/BIDS/21a/install_bssr.py && python install_bssr.py

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd / && wget -qO- http://brainsuite.org/data/BIDS/21a/bfp_083121c.tar.gz | tar xvz
RUN cd / && wget -qO- http://brainsuite.org/data/BIDS/21a/bfp_ver4p01_t1distcorr.tar.gz| tar xvz
RUN rm -rf bfp_ver4p01_t1distcorr/supp_data && mv bfp_ver4p01_t1distcorr/* bfp
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

#COPY bfp/standard/MNI152_T1_2mm.nii.gz /usr/share/fsl/5.0/data/standard/
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

