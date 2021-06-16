# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import uuid
from ast import literal_eval
from datetime import datetime, timezone
from json import dumps

import config_utils
import cv2
import IPCUtils as ipc_utils
import numpy as np
from agent_pb2 import (
    CaptureDataRequest,
    LoadModelRequest,
    PredictRequest,
    Tensor,
    TensorMetadata,
    UnLoadModelRequest,
)

config_utils.logger.info("Using np from '{}'.".format(np.__file__))
config_utils.logger.info("Using cv2 from '{}'.".format(cv2.__file__))

# Read labels file
with open(config_utils.LABELS_FILE, "r") as f:
    labels = literal_eval(f.read())


def transform_image(im):
    if len(im.shape) == 2:
        im = np.expand_dims(im, axis=2)
        nchannels = 1
    elif len(im.shape) == 3:
        nchannels = im.shape[2]
    else:
        raise Exception("Unknown image structure")
    if nchannels == 1:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
    elif nchannels == 4:
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGB)
    elif nchannels == 3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return im


def predict_from_image(image):
    r"""
    Resize the image to the trained model input shape and predict using it.

    :param image: numpy array of the image passed in for inference
    """
    img_data = transform_image(image)
    img_data = cv2.resize(img_data, config_utils.SHAPE)
    img_data = img_data[:, :, (2, 1, 0)].astype(np.float32)
    img_data -= np.array([123, 117, 104])
    img_data = np.expand_dims(img_data, axis=0)
    predict(img_data)


def load_image(image_path):
    r"""
    Validates the image type irrespective of its case. For eg. both .PNG and .png are valid image types.
    Also, accepts numpy array images.

    :param image_path: path of the image on the device.
    :return: a numpy array of shape (1, input_shape_x, input_shape_y, no_of_channels)
    """
    # Case insenstive check of the image type.
    img_lower = image_path.lower()
    if (
        img_lower.endswith(
            ".jpg",
            -4,
        )
        or img_lower.endswith(
            ".png",
            -4,
        )
        or img_lower.endswith(
            ".jpeg",
            -5,
        )
    ):
        try:
            image_data = cv2.imread(image_path)
        except Exception as e:
            config_utils.logger.error(
                "Unable to read the image at: {}. Error: {}".format(image_path, e)
            )
            exit(1)
    elif img_lower.endswith(
        ".npy",
        -4,
    ):
        image_data = np.load(image_path)
    else:
        config_utils.logger.error("Images of format jpg, jpeg, png and npy are only supported.")
        exit(1)
    return image_data


def load_model(name, url):
    load_request = LoadModelRequest()
    load_request.url = url
    load_request.name = name
    config_utils.agent_client.LoadModel(load_request)


def unload_model(name):
    unload_request = UnLoadModelRequest()
    unload_request.name = name
    config_utils.agent_client.UnLoadModel(unload_request)


def predict(image_data):
    PAYLOAD = {}
    PAYLOAD["timestamp"] = str(datetime.now(tz=timezone.utc))
    PAYLOAD["inference-type"] = "image-classification"
    PAYLOAD["inference-description"] = "Top {} predictions with score {} or above ".format(
        config_utils.MAX_NO_OF_RESULTS, config_utils.SCORE_THRESHOLD
    )
    PAYLOAD["inference-results"] = []
    input_tensors = [
        Tensor(
            tensor_metadata=TensorMetadata(
                name=config_utils.tensor_name,
                data_type=5,
                shape=config_utils.tensor_shape,
            ),
            byte_data=image_data.tobytes(),
        )
    ]
    request = PredictRequest(
        name=config_utils.MODEL_NAME,
        tensors=input_tensors,
    )
    response = config_utils.agent_client.Predict(request)
    output_tensors = response.tensors

    capture_data(input_tensors, output_tensors)

    predictions = []
    for t in output_tensors:
        deserialized_bytes = np.frombuffer(t.byte_data, dtype=np.float32)
        predictions.append(np.asarray(deserialized_bytes).tolist())
    probabilities = predictions[0]
    sort_classes_by_probability = np.argsort(probabilities)[::-1]
    for i in sort_classes_by_probability[: config_utils.MAX_NO_OF_RESULTS]:
        if probabilities[i] >= config_utils.SCORE_THRESHOLD:
            result = {"Label": str(labels[i]), "Score": str(probabilities[i])}
            PAYLOAD["inference-results"].append(result)
    config_utils.logger.info(dumps(PAYLOAD))
    if config_utils.TOPIC.strip() != "":
        ipc_utils.IPCUtils().publish_results_to_cloud(PAYLOAD)
    else:
        config_utils.logger.info("No topic set to publish the inference results to the cloud.")


def capture_data(input_tensors, output_tensors):
    capture_id = uuid.uuid4()
    capture_data_request = CaptureDataRequest(
        model_name=config_utils.MODEL_NAME,
        capture_id=str(capture_id),
        input_tensors=input_tensors,
        output_tensors=output_tensors,
    )
    config_utils.logger.info("Capturing the data...")
    capture_data_response = config_utils.agent_client.CaptureData(capture_data_request)
    config_utils.logger.info(capture_data_response)
