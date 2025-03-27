FROM ubuntu:latest

# Set working directory
WORKDIR /scratch

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York
ENV HOME=/home

# Set default command to be the bash shell
ENTRYPOINT ["bash"]

RUN apt-get update && \
    apt-get install -y curl wget && \
    rm -rf /var/lib/apt/lists/*

# Install everything else with Pixi:
# --------------------------------
# 1) copy the required dependency and configuration file into the image
COPY pyproject.toml $HOME/pyproject.toml
COPY pixi.lock $HOME/pixi.lock

# 2) install pixi
RUN cd $HOME && PIXI_ARCH=x86_64 curl -fsSL https://pixi.sh/install.sh | bash

# 3) make sure pixi and pixi installs are on the $PATH
ENV PATH=$PATH:$HOME/.pixi/bin

# 4) install everything else with pixi
#  # && pixi clean cache --assume-yes
RUN cd $HOME && pixi shell --frozen

# 5) modify the shell config so that each container launches within the pixi env
RUN echo "export PATH=$PATH:$HOME/.pixi/envs/default/bin" >> $HOME/.bashrc

# 6) modify some nextflow environment variables
RUN echo "export NXF_CACHE_DIR=/scratch" >> $HOME/.bashrc
RUN echo "export NXF_HOME=/scratch" >> $HOME/.bashrc

