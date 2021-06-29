# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import platform
from ast import literal_eval
from datetime import datetime
from io import BytesIO
from json import dumps
from math import floor
from os import path
from sys import modules
from time import sleep

import config_utils
import IPCUtils as ipc_utils
from cv2 import (
    COLOR_BGR2RGB,
    COLOR_BGRA2RGB,
    COLOR_GRAY2RGB,
    FONT_HERSHEY_SIMPLEX,
    IMWRITE_JPEG_QUALITY,
    VideoCapture,
    cvtColor,
    destroyAllWindows,
    imdecode,
    imread,
    imwrite,
    putText,
    rectangle,
    resize,
)
from dlr import DLRModel
from numpy import (
    argsort,
    array,
    expand_dims,
    float32,
    frombuffer,
    fromstring,
    load,
    transpose,
    uint8,
)

config_utils.logger.info("Using dlr from '{}'.".format(modules[DLRModel.__module__].__file__))
config_utils.logger.info("Using np from '{}'.".format(modules[argsort.__module__].__file__))
config_utils.logger.info("Using cv2 from '{}'.".format(modules[VideoCapture.__module__].__file__))

# Read labels file
with open(config_utils.LABELS, "r") as f:
    labels = literal_eval(f.read())

dlr_model = DLRModel(config_utils.MODEL_DIR, config_utils.DEFAULT_ACCELERATOR)


def transform_image(im):
    if len(im.shape) == 2:
        height, width = im.shape[:2]
        im = expand_dims(im, axis=2)
        nchannels = 1
    elif len(im.shape) == 3:
        height, width, nchannels = im.shape[:3]
    else:
        raise Exception("Unknown image structure")
    if nchannels == 1:
        im = cvtColor(im, COLOR_GRAY2RGB)
    elif nchannels == 4:
        im = cvtColor(im, COLOR_BGRA2RGB)
    elif nchannels == 3:
        im = cvtColor(im, COLOR_BGR2RGB)
    return im


def enable_camera():
    if platform.machine() == "armv7l":  # RaspBerry Pi
        import picamera

        config_utils.CAMERA = picamera.PiCamera()
    elif platform.machine() == "aarch64":  # Nvidia Jetson Nano
        config_utils.CAMERA = VideoCapture(
            "nvarguscamerasrc ! video/x-raw(memory:NVMM),"
            + "width=(int)1920, height=(int)1080, format=(string)NV12,"
            + "framerate=(fraction)30/1 ! nvvidconv flip-method=2 !"
            + "video/x-raw, width=(int)1920, height=(int)1080,"
            + "format=(string)BGRx ! videoconvert ! appsink"
        )
    elif platform.machine() == "x86_64":  # Deeplens
        import awscam

        config_utils.CAMERA = awscam


def draw_bounding_boxes(original_image, inference_results):
    r"""
    Overlays inferred bounding boxes on original image and writes a copy to image_dir

    :param original_image: numpy array of the original image
    :param inference_results: JSON object containing inference results
    """

    output_image = original_image
    height, width, channels = output_image.shape
    scale_factor_x = width / config_utils.WIDTH
    scale_factor_y = height / config_utils.HEIGHT

    config_utils.logger.info(inference_results)

    for result in inference_results:
        boundaries = fromstring(result["Boundaries"][1:-1], dtype=float, sep=" ")
        box_label = "{} : {}".format(result["Label"], result["Score"])
        x_min = floor(boundaries[0] * scale_factor_x)
        y_min = floor(boundaries[1] * scale_factor_y)
        x_max = floor(boundaries[2] * scale_factor_x)
        y_max = floor(boundaries[3] * scale_factor_y)

        # Draw bounding box
        rectangle(
            img=output_image,
            pt1=(x_min, y_min),
            pt2=(x_max, y_max),
            color=(0, 0, 0),
            thickness=2,
        )

        # Draw black text outline
        putText(
            img=output_image,
            text=box_label,
            org=(
                x_min,
                int(y_min - (0.02 * height)),
            ),  # Draw text above top left of box
            fontFace=FONT_HERSHEY_SIMPLEX,
            fontScale=0.6,
            color=(255, 255, 255),
            thickness=3,
        )
        # Draw white text
        putText(
            img=output_image,
            text=box_label,
            org=(
                x_min,
                int(y_min - (0.02 * height)),
            ),  # Draw text above top left of box
            fontFace=FONT_HERSHEY_SIMPLEX,
            fontScale=0.6,
            color=(0, 0, 0),
            thickness=2,
        )

    output_path = path.join(
        config_utils.BOUNDED_OUTPUT_DIR, config_utils.DEFAULT_BOUNDED_OUTPUT_IMAGE_NAME
    )
    imwrite(output_path, output_image, [IMWRITE_JPEG_QUALITY, 100])
    config_utils.logger.info("Output image with bounding boxes to {}".format(output_path))


def predict(image_data):
    r"""
    Performs object detection and predicts using the model.

    :param image_data: numpy array of the resized image passed in for inference.
    :return: JSON object of inference results
    """
    PAYLOAD = {}
    PAYLOAD["timestamp"] = str(datetime.now())
    PAYLOAD["inference-type"] = "object-detection"
    PAYLOAD["inference-description"] = "Top {} predictions with score {} or above ".format(
        config_utils.MAX_NO_OF_RESULTS, config_utils.SCORE_THRESHOLD
    )
    PAYLOAD["inference-results"] = []
    try:
        # Run DLR to perform inference with DLC optimized model
        ids, scores, bboxes = dlr_model.run(image_data)
        predicted = []
        for i, cl in enumerate(scores[0]):
            if len(predicted) == config_utils.MAX_NO_OF_RESULTS:
                break
            class_id = int(ids[0][i][0])
            if cl[0] >= config_utils.SCORE_THRESHOLD:
                predicted.append(class_id)
                result = {
                    "Label": str(labels[class_id]),
                    "Score": str(cl[0]),
                    "Boundaries": str(bboxes[0][i]),
                }
                PAYLOAD["inference-results"].append(result)
        config_utils.logger.info(dumps(PAYLOAD))

        if config_utils.TOPIC.strip() != "":
            ipc_utils.IPCUtils().publish_results_to_cloud(PAYLOAD)
        else:
            config_utils.logger.info("No topic set to publish the inference results to the cloud.")

        return PAYLOAD["inference-results"]
    except Exception as e:
        config_utils.logger.error("Exception occured during prediction: {}".format(e))


def predict_from_image(image):
    r"""
    Resize the image to the trained model input shape and predict using it.

    :param image: numpy array of the image passed in for inference
    """
    img_data = transform_image(image)
    img_data = resize(img_data, config_utils.SHAPE)
    inference_results = predict(img_data)
    draw_bounding_boxes(image, inference_results)


def predict_from_cam():
    r"""
    Captures an image using camera and sends it for prediction
    """
    cvimage = None
    if config_utils.CAMERA is None:
        config_utils.logger.error("Unable to support camera.")
        return
    if platform.machine() == "armv7l":  # RaspBerry Pi
        stream = BytesIO()
        config_utils.CAMERA.start_preview()
        sleep(2)
        config_utils.CAMERA.capture(stream, format="jpeg")
        # Construct a numpy array from the stream
        data = fromstring(stream.getvalue(), dtype=uint8)
        # "Decode" the image from the array, preserving colour
        cvimage = imdecode(data, 1)
    elif platform.machine() == "aarch64":  # Nvidia Jetson TX
        if config_utils.CAMERA.isOpened():
            ret, cvimage = config_utils.CAMERA.read()
            destroyAllWindows()
        else:
            raise RuntimeError("Cannot open the camera")
    elif platform.machine() == "x86_64":  # Deeplens
        ret, cvimage = config_utils.CAMERA.getLastFrame()
        if ret == False:
            raise RuntimeError("Failed to get frame from the stream")
    if cvimage is not None:
        return predict_from_image(cvimage)
    else:
        config_utils.logger.error("Unable to capture an image using camera")
        exit(1)


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
            image_data = imread(image_path)
        except Exception as e:
            config_utils.logger.error(
                "Unable to read the image at: {}. Error: {}".format(image_path, e)
            )
            exit(1)
    elif img_lower.endswith(
        ".npy",
        -4,
    ):
        image_data = load(image_path)
    else:
        config_utils.logger.error("Images of format jpg,jpeg,png and npy are only supported.")
        exit(1)
    return image_data
