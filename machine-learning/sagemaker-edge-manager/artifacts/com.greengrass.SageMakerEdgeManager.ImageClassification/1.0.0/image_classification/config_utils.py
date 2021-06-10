# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import sys
from os import environ, path
from threading import Condition

from awsiot.greengrasscoreipc.model import QOS

# Set all the constants
SCORE_THRESHOLD = 0.3
MAX_NO_OF_RESULTS = 5
SIZE = 224
SHAPE = (SIZE, SIZE)
QOS_TYPE = QOS.AT_LEAST_ONCE
TIMEOUT = 10

# Intialize all the variables with default values
DEFAULT_IMAGE_NAME = "cat.jpeg"
DEFAULT_PREDICTION_INTERVAL_SECS = 3600
SCHEDULED_THREAD = None
TOPIC = ""

# Get a logger
logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

condition = Condition()

# Get the model directory and images directory from the env variables.
IMAGE_DIR = path.expandvars(environ.get("DEFAULT_SMEM_IC_IMAGE_DIR"))
MODEL_DIR = path.expandvars(environ.get("SMEM_IC_MODEL_DIR"))
LABELS_FILE = path.expandvars(environ.get("SMEM_IC_LABELS"))
# Get sagemaker edge manager config
MODEL_NAME = "resnet"
tensor_name = "data"
tensor_shape = [1, SIZE, SIZE, 3]

agent_client = None
edge_agent_component_name = "aws.greengrass.SageMakerEdgeManager"
edge_agent_socket_change = True
inference_component_name = "com.greengrass.SageMakerEdgeManager.ImageClassification"
