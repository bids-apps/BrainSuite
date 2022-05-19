FROM yeunkim/bidsapphead

ENV BrainSuiteVersion="21a"
RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/install_dep.py
RUN python install_dep.py

# BrainSuite
RUN wget -q http://brainsuite.org/data/BIDS/BrainSuite${BrainSuiteVersion}.BIDS.tgz && \
    tar -xzf /BrainSuite${BrainSuiteVersion}.BIDS.tgz && \
    mv /BrainSuite${BrainSuiteVersion} /opt && \
    cd /opt/BrainSuite${BrainSuiteVersion}/bin && \
    chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion} && \
    cd / && \
    rm BrainSuite${BrainSuiteVersion}.BIDS.tgz

RUN cd / && wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bssr_0.3.1b.tar.gz && tar xzf bssr_0.3.1b.tar.gz
#RUN cd / && wget http://brainsuite.org/wp-content/uploads/2021/11/bssr_0.3.2.tar.gz
RUN wget http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/install_bssr.py && python install_bssr.py

RUN chmod -R ugo+r /opt/BrainSuite${BrainSuiteVersion}

ENV PATH=/opt/BrainSuite${BrainSuiteVersion}/bin/:/opt/BrainSuite${BrainSuiteVersion}/svreg/bin/:/opt/BrainSuite${BrainSuiteVersion}/bdp/:${PATH}

RUN cd /opt/BrainSuite${BrainSuiteVersion}/bin/ && \
    wget -q http://shattuck.bmap.ucla.edu/bids/volslice21a_x86_64-pc-linux-gnu && \
    wget -q http://shattuck.bmap.ucla.edu/bids/renderdfs21a_x86_64-pc-linux-gnu && \
    ln -s volslice21a_x86_64-pc-linux-gnu volslice && \
    ln -s renderdfs21a_x86_64-pc-linux-gnu renderdfs && \
    chmod -R ugo+xr /opt/BrainSuite${BrainSuiteVersion}/bin

RUN cd / && wget -qO- http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bfp_083121c.tar.gz | tar xvz
RUN cd / && wget -qO- http://users.bmap.ucla.edu/~yeunkim/brainsuitebids/bfp_ver4p01_t1distcorr.tar.gz| tar xvz
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

