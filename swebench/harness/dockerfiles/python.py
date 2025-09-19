
_DOCKERFILE_BASE_PY = r"""
FROM --platform=${platform} ubuntu:${ubuntu_version}

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends         wget         git         build-essential         libffi-dev         libtiff-dev         python3         python3-pip         python-is-python3         jq         curl         ca-certificates         locales         locales-all         tzdata &&         update-ca-certificates &&         rm -rf /var/lib/apt/lists/*

# Install Miniforge for x86_64 deterministically, with a fallback that ignores TLS errors
RUN /bin/bash -lc 'set -euxo pipefail;         curl -fsSL --retry 3 --connect-timeout 30           https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh           -o /tmp/miniforge.sh         || curl -fsSLk --retry 3 --connect-timeout 30           https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh           -o /tmp/miniforge.sh;         bash /tmp/miniforge.sh -b -p /opt/miniconda3;         rm -f /tmp/miniforge.sh'

# Put conda on PATH and initialize
ENV PATH=/opt/miniconda3/bin:$PATH
RUN /opt/miniconda3/bin/conda init --all || true
RUN /opt/miniconda3/bin/conda config --system --prepend channels conda-forge || true

# Non-root user (kept from original)
RUN adduser --disabled-password --gecos 'dog' nonroot
"""

_DOCKERFILE_ENV_PY = r"""
FROM --platform=${platform} ${base_image_key}

# Bring in the env setup script
COPY ./setup_env.sh /root/
RUN sed -i -e 's/\r$//' /root/setup_env.sh && chmod +x /root/setup_env.sh

# Run with conda available in this shell; avoid $-vars in the template
RUN /bin/bash -lc 'set -euxo pipefail; \        
source /opt/miniconda3/etc/profile.d/conda.sh || true; \        
conda --version || true; \
conda config --system --set ssl_verify false || true; \        
conda config --system --prepend channels conda-forge || true;  \       
conda install -n base -y -c conda-forge mamba || true;  \       
/root/setup_env.sh'

WORKDIR /testbed/

# Auto-activate the testbed env for interactive shells
RUN echo "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed" > /root/.bashrc
"""

_DOCKERFILE_INSTANCE_PY = r"""
FROM --platform=${platform} ${env_image_name}

COPY ./setup_repo.sh /root/
RUN sed -i -e 's/\r$//' /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""