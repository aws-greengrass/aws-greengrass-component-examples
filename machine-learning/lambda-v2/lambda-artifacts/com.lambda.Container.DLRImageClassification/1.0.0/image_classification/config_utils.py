# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from logging import getLogger
from os import environ, path
from pathlib import Path
from threading import Condition

from awsiot.greengrasscoreipc.model import QOS

# Set all the constants
SCORE_THRESHOLD = 0.3
MAX_NO_OF_RESULTS = 5
SHAPE = (224, 224)
QOS_TYPE = QOS.AT_LEAST_ONCE
TIMEOUT = 10
SCORE_CONVERTER = 255

# Intialize all the variables with default values
CAMERA = None
DEFAULT_ACCELERATOR = "cpu"
DEFAULT_IMAGE_NAME = "cat.jpeg"
DEFAULT_PREDICTION_INTERVAL_SECS = 3600
DEFAULT_USE_CAMERA = "false"
SCHEDULED_THREAD = None
TOPIC = ""

# Get a logger
logger = getLogger()

# Get the model directory and images directory from the env variables.
MODEL_DIR = path.expandvars(path.join(environ["PWD"], environ.get("DLR_IC_MODEL_DIR")))
artifacts_path = Path(__file__).parent.absolute()
IMAGE_DIR = path.join(artifacts_path, "sample_images")
LABELS = path.expandvars(environ.get("DLR_IC_LABELS"))

condition = Condition()
