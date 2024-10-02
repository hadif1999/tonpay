FROM ubuntu:20.04

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata

RUN apt install -y build-essential cmake clang-6.0 openssl libssl-dev zlib1g-dev gperf wget git curl libreadline-dev ccache libmicrohttpd-dev

# build tonlib
WORKDIR /

# remove /tree/<commit> to build master branch
RUN git clone --recurse-submodules https://github.com/newton-blockchain/ton.git

# fix lib version and patch logging
WORKDIR /ton
#RUN git checkout 9875f02ef4ceba5b065d5e63c920f91aec73224e
#COPY infrastructure/tonlib.patch /ton/
#RUN git apply /ton/tonlib.patch
#RUN cat /ton/crypto/smc-envelope/SmartContract.h

RUN mkdir /ton/build
WORKDIR /ton/build
ENV CC=clang-6.0
ENV CX=clang++-6.0
RUN cmake -DCMAKE_BUILD_TYPE=Release ..
#RUN cmake --build . --target tonlibjson

COPY . .
RUN apt update && apt-get -y install python3 python3-dev python3-pip jq apt-utils
RUN pip3 install -r requirements.txt
#RUN make -kB && make test-* && make install test_*
#RUN bash scripts/setup.sh 
#RUN bash scripts/update_init_block.sh

#RUN cd pytonlib && ./build_tonlib.sh  # docker is needed

#RUN git clone https://github.com/wolfssl/wolfssl.git && cd wolfssl/ && ./autogen.sh && ./configure --enable-sha512

#RUN apt-get install -y git autoconf libtool && git clone https://github.com/wolfssl/wolfssl.git
#RUN cd wolfssl/ && ./autogen.sh && ./configure --enable-sha512 && make && make install && ldconfig

ENTRYPOINT [ "/bin/bash"]
