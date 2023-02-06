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


RUN echo "set enable-bracketed-paste off" >> ~/.inputrc

ENTRYPOINT ["/BrainSuite/run.py"]

