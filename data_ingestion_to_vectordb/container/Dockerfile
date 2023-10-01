ARG REGION=us-east-1

# SageMaker PyTorch image for INFERENCE
# For more information, see https://github.com/aws/deep-learning-containers/blob/master/available_images.md
FROM 763104351884.dkr.ecr.$REGION.amazonaws.com/pytorch-inference:2.0.1-cpu-py310-ubuntu20.04-sagemaker

# pip leaves the install caches populated which uses a
# significant amount of space. These optimizations save a fair
# amount of space in the image, which reduces start up time.
RUN pip install --no-cache-dir -U pip && pip --no-cache-dir install opensearch-py==2.2.0 \
    transformers==4.32.1 \
    farm-haystack[aws] \
    farm-haystack[preprocessing] \
    farm-haystack[opensearch] \
    farm-haystack[inference]

RUN pip freeze

ENV PATH="/opt/ml/code:${PATH}"

# this environment variable is used by the SageMaker PyTorch container to determine our user code directory.
ENV SAGEMAKER_SUBMIT_DIRECTORY /opt/ml/code

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE