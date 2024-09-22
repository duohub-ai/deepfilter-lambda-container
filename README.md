# DeepFilter Lambda Container

This project implements a Lambda function using a container image to enhance audio files using the DeepFilter model.

## Table of Contents

1. [**DeepFilter Lambda Container**](#deepfilter-lambda-container)
2. [**Dockerfile**](#dockerfile)
   1. [Key Components of the Dockerfile](#key-components-of-the-dockerfile)
      1. [Base Image](#base-image)
      2. [System Dependencies](#system-dependencies)
      3. [HDF5 Installation](#hdf5-installation)
      4. [Rust and Cargo Installation](#rust-and-cargo-installation)
      5. [FFmpeg Installation](#ffmpeg-installation)
      6. [PyTorch and torchaudio Installation](#pytorch-and-torchaudio-installation)
      7. [Python Dependencies](#python-dependencies)
      8. [Environment Variables](#environment-variables)
      9. [Code and Model Copying](#code-and-model-copying)
      10. [CMD Specification](#cmd-specification)
3. [**Lambda Function**](#lambda-function)
   1. [Model Initialization](#model-initialization)
      1. [Copying Model Files](#copying-model-files)
      2. [Loading the Model](#loading-the-model)
   2. [Placeholder Functions](#placeholder-functions)
      1. [Get File Record and File from S3](#get-file-record-and-file-from-s3)
      2. [Enhance Audio](#enhance-audio)
      3. [Convert to MP3](#convert-to-mp3)
      4. [Upload to S3](#upload-to-s3)
      5. [Create File Record](#create-file-record)
4. [**Deploying the Lambda Function**](#deploying-the-lambda-function)
   1. [Build the Docker Image](#build-the-docker-image)
   2. [Push the Docker Image to ECR](#push-the-docker-image-to-ecr)
   3. [Deploy the Lambda Function](#deploy-the-lambda-function)


## Dockerfile

Our Dockerfile is structured to create an efficient and functional container for running the DeepFilter model in an AWS Lambda environment. Here's a breakdown of the key components:

### Key Components of the Dockerfile

1. **Base Image**: 
   ```sh
   FROM public.ecr.aws/lambda/python:3.10
   ```
   Use the official AWS Lambda Python 3.10 image as our base, ensuring compatibility with the Lambda environment.

   Why Python 3.10? You can only install numpy >= 2 with Python 3.12, and since DeepFilter relies on an older version of numpy, we need to use Python 3.10.

2. **System Dependencies**: 
   ```sh
   RUN yum update -y && yum install -y git wget tar xz gcc gcc-c++ make ...
   ```
   Update the system and install essential build tools and libraries needed for compiling certain Python packages and dependencies.

3. **HDF5 Installation**: 
   ```sh
   ENV HDF5_VERSION=1.12.2
   RUN wget https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.12/hdf5-${HDF5_VERSION}/src/hdf5-${HDF5_VERSION}.tar.gz ...
   ```
   Install HDF5 from source, which is a system dependency for DeepFilter.

4. **Rust and Cargo Installation**: 
   ```sh
   RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
   ```
   Install Rust and Cargo, which are required for building some Python packages with Rust extensions.

5. **FFmpeg Installation**: 
   ```sh
   RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz ...
   ```
   Download and install a static build of FFmpeg.

   Why a static build? Yum, the package manager for Amazon Linux 2, doesn't have FFmpeg.

6. **PyTorch and torchaudio Installation**: 
   ```sh
   RUN pip install torch==2.0.0 torchaudio==2.0.1 -f https://download.pytorch.org/whl/cpu/torch_stable.html
   ```
   Install specific versions of PyTorch and torchaudio optimized for CPU usage. Install these specific versions to run DeepFilter on CPU.

7. **Python Dependencies**: 
   ```sh
   RUN pip install icecream loguru numpy ptflops requests packaging sympy colorama pydub boto3 deepfilternet
   ```
   Install various Python packages required for our application, including the DeepFilterNet library.

8. **Environment Variables**: 
   ```sh
   ENV RUSTFLAGS="-L ${HDF5_LIBDIR}" \
       LIBHDF5_LIBDIR=${HDF5_LIBDIR} \
       LIBHDF5_INCLUDEDIR=${HDF5_INCLUDEDIR}
   ```
   Set environment variables necessary for building packages that depend on HDF5.

9. **Code and Model Copying**: 
   ```sh
   COPY main.py ${LAMBDA_TASK_ROOT}/
   COPY modules/ ${LAMBDA_TASK_ROOT}/modules/
   COPY models/ /opt/deepfilter_models/
   ```
   Copy application code and the DeepFilter models into the container.

10. **CMD Specification**: 
    ```sh
    CMD [ "main.lambda_handler" ]
    ```
    We specify the Lambda handler function as the container's entry point.

This Dockerfile creates a comprehensive environment with all necessary dependencies and configurations to run our DeepFilter Lambda function efficiently.

## Lambda Function

The Lambda function is designed to work within the constraints of the AWS Lambda environment, particularly the read-only filesystem outside of `/tmp`.

### Model Initialization

The model initialization process is handled in two steps to work around the read-only nature of the Lambda environment:

1. **Copying Model Files**: When the Lambda function starts, it first copies the model files from `/opt/deepfilter_models/` (read-only) to `/tmp/deepfilter_models/` (writable).

   ```python
   def copy_model_files():
       if not os.path.exists(TMP_MODEL_DIR):
           shutil.copytree('/opt/deepfilter_models/', TMP_MODEL_DIR)
   ```
Lambda environments are read-only, so we need to copy the model files to a writable directory.

2. **Loading the Model**: After copying, the function loads the model from the `/tmp` directory.

   ```python
   def load_deepfilter_model(model, df_state):
       if model is None or df_state is None:
           copy_model_files()
           model, df_state, _ = init_df(model_base_dir=TMP_MODEL_DIR)
   ```
### Placeholder functions

Placeholder  functions exist where you might add your own fetching and processing logic. 

3. **Get File record and File from S3**: The function fetches the file record and file from S3.
4. **Enhance Audio**: The function enhances the audio file using the DeepFilter model.
5. **Convert to MP3**: The function converts the enhanced audio file to MP3 format.
6. **Upload to S3**: The function uploads the cleaned MP3 file to S3.
7. **Create File Record**: The function creates a file record in the database.

By using this approach, we create an efficient and reliable system for running the DeepFilter model in a serverless environment.


# Deploying the Lambda Function

Notice the function declaration in the `serverless.yml` file. First add the appropriate definitions to your serverless stack.

```yml
functions:
  cleanAudio:
    image: {accountID}.dkr.ecr.eu-west-2.amazonaws.com/lambda-clean-audio:latest
    timeout: 600
    memorySize: 2048
    ephemeralStorageSize: 4096
    environment:
      TABLE_NAME: Audio-${self:provider.stage}
      STAGE: ${self:provider.stage}
```

To deploy the Lambda function, you need to have the AWS CLI installed and configured with the appropriate permissions.

1. **Build the Docker Image**:
   ```sh
   docker build -t deepfilter-lambda-container .
   ```

2. **Push the Docker Image to ECR**:
   ```sh
   aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin {accountID}.dkr.ecr.{region}.amazonaws.com
   docker tag deepfilter-lambda-container:latest {accountID}.dkr.ecr.{region}.amazonaws.com/lambda-clean-audio:latest
   docker push {accountID}.dkr.ecr.{region}.amazonaws.com/lambda-clean-audio:latest
   ```

3. **Deploy the Lambda Function**:
   ```
   serverless deploy
   ```

This will deploy the Lambda function to your AWS account.

## Provisioned Concurrency

With container lambdas, cold starts can be a problem. You can pre-warm your Lambda, but it's not the ideal solution. 

Provisioned concurrency is a feature of AWS Lambda that allows you to reserve a specified number of concurrent executions for your function. This can help achieve consistent performance and lower costs by ensuring that your function has the resources it needs to handle requests quickly and efficiently.

[See More in the AWS Guide](https://docs.aws.amazon.com/lambda/latest/operatorguide/execution-environments.html#cold-start-latency)

![Provisioned Concurrency](https://docs.aws.amazon.com/images/lambda/latest/operatorguide/images/perf-optimize-figure-4.png)



## Project Structure

The file tree is as follows:

```
.
├── Dockerfile
├── main.py
├── models
│   ├── checkpoints
│   │   └── model_120.ckpt.best
│   └── config.ini
├── modules
│   ├── __init__.py
│   ├── file.py
│   ├── init.py
│   └── s3.py
├── poetry.lock
├── push.sh
└── pyproject.toml
```
