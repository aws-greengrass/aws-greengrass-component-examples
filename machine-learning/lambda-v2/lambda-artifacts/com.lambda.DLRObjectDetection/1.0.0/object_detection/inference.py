# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import makedirs, path
from threading import Timer, Thread
from time import sleep

import config_utils
import IPCUtils as ipc_utils
import prediction_utils


def set_configuration(config):
    r"""
    Sets a new config object with the combination of updated and default configuration as applicable.
    Calls inference code with the new config and indicates that the configuration changed.
    """
    new_config = {}

    if "ImageName" in config:
        new_config["image_name"] = config["ImageName"]
    else:
        new_config["image_name"] = config_utils.DEFAULT_IMAGE_NAME
        config_utils.logger.warning(
            "Using default image name: {}".format(config_utils.DEFAULT_IMAGE_NAME)
        )

    if "ImageDirectory" in config:
        new_config["image_dir"] = config["ImageDirectory"]
    else:
        new_config["image_dir"] = config_utils.IMAGE_DIR
        config_utils.logger.warning(
            "Using default image directory: {}".format(config_utils.IMAGE_DIR)
        )

    if "InferenceInterval" in config:
        new_config["prediction_interval_secs"] = config["InferenceInterval"]
    else:
        new_config["prediction_interval_secs"] = config_utils.DEFAULT_PREDICTION_INTERVAL_SECS
        config_utils.logger.warning(
            "Using default inference interval: {}".format(
                config_utils.DEFAULT_PREDICTION_INTERVAL_SECS
            )
        )

    if "UseCamera" in config:
        new_config["use_camera"] = config["UseCamera"]
    else:
        new_config["use_camera"] = config_utils.DEFAULT_USE_CAMERA
        config_utils.logger.warning(
            "Using default camera: {}".format(config_utils.DEFAULT_USE_CAMERA)
        )

    if "PublishResultsOnTopic" in config:
        config_utils.TOPIC = config["PublishResultsOnTopic"]
    else:
        config_utils.TOPIC = ""
        config_utils.logger.warning("Topic to publish inference results is empty.")

    if new_config["use_camera"].lower() == "true":
        prediction_utils.enable_camera()

    new_config["image"] = prediction_utils.load_image(
        path.join(new_config["image_dir"], new_config["image_name"])
    )

    # Create the directory for output images with overlaid bounding boxes, if it does not exist already
    makedirs(config_utils.BOUNDED_OUTPUT_DIR, exist_ok=True)

    # Run inference with the updated config indicating the config change.
    run_inference(new_config, True)


def run_inference(new_config, config_changed):
    r"""
    Uses the new config to run inference.

    :param new_config: Updated config if the config changed. Else, the last updated config.
    :param config_changed: Is True when run_inference is called after setting the newly updated config.
    Is False if run_inference is called using scheduled thread as the config hasn't changed.
    """

    if config_changed:
        if config_utils.SCHEDULED_THREAD is not None:
            config_utils.SCHEDULED_THREAD.cancel()
        config_changed = False
    if new_config["use_camera"].lower() == "true":
        prediction_utils.predict_from_cam()
    else:
        prediction_utils.predict_from_image(new_config["image"])
    config_utils.SCHEDULED_THREAD = Timer(
        int(new_config["prediction_interval_secs"]),
        run_inference,
        [new_config, config_changed],
    )
    config_utils.SCHEDULED_THREAD.start()

def wait_for_config_changes():
    with config_utils.condition:
        config_utils.condition.wait()
        set_configuration(ipc.get_configuration())
    wait_for_config_changes()

ipc = ipc_utils.IPCUtils()

# Get intial configuration from the recipe and run inference for the first time.
set_configuration(ipc.get_configuration())

# Subscribe to the subsequent configuration changes
ipc.get_config_updates()

Thread(
    target=wait_for_config_changes,
    args=(),
).start()

    
def lambda_handler(event, context):
    return 