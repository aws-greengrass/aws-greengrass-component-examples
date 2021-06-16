# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from os import path
from threading import Thread, Timer
from time import sleep

import config_utils
import IPCUtils as ipc_utils
from agent_pb2_grpc import AgentStub
from grpc import insecure_channel
from prediction_utils import load_image, load_model, predict_from_image, unload_model


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

    if "PublishResultsOnTopic" in config:
        config_utils.TOPIC = config["PublishResultsOnTopic"]
    else:
        config_utils.TOPIC = ""
        config_utils.logger.warning("Topic to publish inference results is empty.")

    if config_utils.edge_agent_socket_change:
        config_utils.edge_agent_socket_change = False
        if "UnixSocketName" in config:
            while not path.exists(config["UnixSocketName"]):
                config_utils.logger.info(
                    "Configuration changed. Waiting for the edge agent to create the socket..."
                )
                sleep(1)
            config_utils.agent_client = AgentStub(
                insecure_channel(
                    "unix://{}".format(config["UnixSocketName"]),
                    options=(("grpc.enable_http_proxy", 0),),
                )
            )

            try:
                unload_model(config_utils.MODEL_NAME)
            except Exception as e:
                config_utils.logger.error("Error unloading the model: {}".format(e))

            try:
                load_model(config_utils.MODEL_NAME, config_utils.MODEL_DIR)
            except Exception as e:
                config_utils.logger.error("Error loading the model: {}".format(e))
        else:
            config_utils.logger.error(
                "Unix socket name is not specified. Please specify it to use the edge manager agent."
            )
            exit(1)

    new_config["image"] = load_image(path.join(new_config["image_dir"], new_config["image_name"]))

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
    try:
        predict_from_image(new_config["image"])
    except Exception as e:
        config_utils.logger.error(
            "Error running the inference as the edge agent config changed: {}".format(e)
        )
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
