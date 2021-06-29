# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from logging import INFO, StreamHandler, getLogger
from os import environ, path
from sys import stdout
from pathlib import Path
from awsiot.greengrasscoreipc.model import QOS

# Set all the constants
SCORE_THRESHOLD = 0.3
MAX_NO_OF_RESULTS = 5
HEIGHT = 512
WIDTH = 512
SHAPE = (HEIGHT, WIDTH)
QOS_TYPE = QOS.AT_LEAST_ONCE
TIMEOUT = 10
SCORE_CONVERTER = 255

# Intialize all the variables with default values
CAMERA = None
DEFAULT_ACCELERATOR = "cpu"
DEFAULT_IMAGE_NAME = "objects.jpeg"
DEFAULT_BOUNDED_OUTPUT_IMAGE_NAME = "bounded_output.jpeg"
DEFAULT_PREDICTION_INTERVAL_SECS = 3600
DEFAULT_USE_CAMERA = "false"
UPDATED_CONFIG = False
SCHEDULED_THREAD = None
TOPIC = ""

# Get a logger
logger = getLogger()
handler = StreamHandler(stdout)
logger.setLevel(INFO)
logger.addHandler(handler)

# Get the model directory and images directory from the env variables.
artifacts_path = Path(__file__).parent.absolute()
IMAGE_DIR = IMAGE_DIR = path.join(artifacts_path, "sample_images")
WORK_DIR = path.expandvars(environ.get("PWD"))
MODEL_DIR = path.expandvars(path.join(WORK_DIR, environ.get("DLR_OD_MODEL_DIR")))
BOUNDED_OUTPUT_DIR_NAME = "bounded_output"
BOUNDED_OUTPUT_DIR = path.join(WORK_DIR, BOUNDED_OUTPUT_DIR_NAME)
LABELS =  path.expandvars(environ.get("DLR_OD_LABELS"))