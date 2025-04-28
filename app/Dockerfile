FROM nikolaik/python-nodejs:python3.12-nodejs23-slim AS files

RUN apt-get update && \
    apt-get install curl unzip gzip -y --no-install-recommends  && \
    rm -rf /var/lib/apt/lists/*

# Downloading hg19ToHg38.over.chain.gz file needed for pyliftover into it's cache directory
RUN curl -O "http://hgdownload2.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz"
# RUN gunzip -c hg19ToHg38.over.chain.gz > hg19ToHg38.over.chain

# Downloading and extracting hg38.fa.gz file needed for SpliceAI
RUN curl -O "https://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz"
RUN gunzip -c hg38.fa.gz > hg38.fa

# Downloading and extracting revel-v1.3_all_chromosomes.zip file needed for REVEL
RUN curl -O "https://rothsj06.dmz.hpc.mssm.edu/revel-v1.3_all_chromosomes.zip"
RUN unzip revel-v1.3_all_chromosomes.zip



FROM nikolaik/python-nodejs:python3.12-nodejs23-slim AS final

RUN apt-get update && \
    apt-get install wget -y --no-install-recommends

RUN install -d -m 0755 /etc/apt/keyrings

RUN wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null

RUN echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null

COPY ./mozilla /etc/apt/preferences.d/mozilla

RUN apt-get update && \
    apt-get install redis-server firefox -y --no-install-recommends  && \
    rm -rf /var/lib/apt/lists/*


ARG APP_DIR="/kath/app"

WORKDIR ${APP_DIR}

COPY ./back_end/requirements.txt .
RUN MAKEFLAGS="-j$(nproc)" pip install --no-cache-dir --break-system-packages --root-user-action ignore -r ./requirements.txt

COPY ./front_end/package.json .
RUN npm install && mv ./node_modules /

COPY --link=true --from=files /hg19ToHg38.over.chain.gz     /root/.pyliftover/
COPY --link=true --from=files /hg38.fa                      ./back_end/src/workspace/fasta/
COPY --link=true --from=files /revel_with_transcript_ids    ./back_end/src/workspace/revel

# COPY --link=true ./hg19ToHg38.over.chain.gz     /root/.pyliftover/
# COPY --link=true ./hg38.fa                      ./back_end/src/workspace/fasta/
# COPY --link=true ./revel_with_transcript_ids    ./back_end/src/workspace/revel

COPY ./run.sh ./
COPY ./back_end/ ./back_end/
COPY ./front_end/ ./front_end/

ENTRYPOINT ["./run.sh"]


# # Downloading hg19ToHg38.over.chain.gz file needed for pyliftover into it's cache directory
# # WORKDIR /root/.pyliftover/
# ADD --link http://hgdownload2.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz /
#
# # Downloading and extracting hg38.fa.gz file needed for SpliceAI
# # WORKDIR ${APP_DIR}/back_end/src/workspace/fasta/
# ADD --link https://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz /
# RUN gunzip hg38.fa.gz
#
# # Downloading and extracting revel-v1.3_all_chromosomes.zip file needed for REVEL
# # WORKDIR ${APP_DIR}/back_end/src/workspace/revel
# ADD --link https://rothsj06.dmz.hpc.mssm.edu/revel-v1.3_all_chromosomes.zip /
# RUN unzip revel-v1.3_all_chromosomes.zip
#
# WORKDIR ${APP_DIR}/back_end/src/
# COPY ./back_end/src/scripts/revel.py ./scripts/
# RUN python3 scripts/revel.py workspace/revel/revel_with_transcript_ids workspace/revel/revel_with_transcript_ids.db
