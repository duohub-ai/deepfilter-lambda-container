# Use AWS Lambda Python 3.10 base image
FROM public.ecr.aws/lambda/python:3.10

# Install system dependencies
RUN yum update -y && \
    yum install -y \
    git \
    wget \
    tar \
    xz \
    gcc \
    gcc-c++ \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    zlib-devel \
    pkg-config \
    && yum clean all

# Install HDF5 from source
ENV HDF5_VERSION=1.12.2
RUN wget https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-${HDF5_VERSION}/src/hdf5-${HDF5_VERSION}.tar.gz && \
    tar -xzf hdf5-${HDF5_VERSION}.tar.gz && \
    cd hdf5-${HDF5_VERSION} && \
    ./configure --prefix=/usr/local/hdf5 && \
    make && \
    make install && \
    cd .. && \
    rm -rf hdf5-${HDF5_VERSION} hdf5-${HDF5_VERSION}.tar.gz

# Set HDF5 environment variables
ENV HDF5_DIR=/usr/local/hdf5 \
    HDF5_LIBDIR=/usr/local/hdf5/lib \
    HDF5_INCLUDEDIR=/usr/local/hdf5/include \
    LD_LIBRARY_PATH=/usr/local/hdf5/lib:$LD_LIBRARY_PATH \
    PATH=/usr/local/hdf5/bin:$PATH

# Install Rust and Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install FFmpeg
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz && \
    tar xvf ffmpeg-release-arm64-static.tar.xz && \
    mv ffmpeg-*-arm64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-arm64-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*-arm64-static*

# Clone DeepFilterNet repository to a persistent location
# RUN git clone https://github.com/Rikorose/DeepFilterNet.git /opt/DeepFilterNet

# Install PyTorch and torchaudio
RUN pip install torch==2.0.0 torchaudio==2.0.1 -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install Python dependencies that don't require compilation
RUN pip install numpy pydub boto3 deepfilternet

# Set additional environment variables for the build process
ENV RUSTFLAGS="-L ${HDF5_LIBDIR}" \
    LIBHDF5_LIBDIR=${HDF5_LIBDIR} \
    LIBHDF5_INCLUDEDIR=${HDF5_INCLUDEDIR}

# Debug: Print out key information
RUN echo "HDF5_DIR: $HDF5_DIR" && \
    echo "HDF5_LIBDIR: $HDF5_LIBDIR" && \
    echo "HDF5_INCLUDEDIR: $HDF5_INCLUDEDIR" && \
    echo "PKG_CONFIG_PATH: $PKG_CONFIG_PATH" && \
    ls -l $HDF5_LIBDIR && \
    ls -l $HDF5_INCLUDEDIR

# Set back to Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy function code
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY modules/ ${LAMBDA_TASK_ROOT}/modules/

COPY models/ /opt/deepfilter_models/

# Set the CMD to your handler
CMD [ "main.lambda_handler" ]
