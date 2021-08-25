import platform
from ast import literal_eval
from datetime import datetime
from io import BytesIO
from json import dumps
from sys import modules
from time import sleep

import config_utils
import IPCUtils as ipc_utils
from cv2 import VideoCapture, destroyAllWindows, imdecode, imread, resize
from dlr import DLRModel
from numpy import argsort, frombuffer, fromstring, load, uint8

config_utils.logger.info("Using dlr from '{}'.".format(modules[DLRModel.__module__].__file__))
config_utils.logger.info("Using np from '{}'.".format(modules[argsort.__module__].__file__))
config_utils.logger.info("Using cv2 from '{}'.".format(modules[VideoCapture.__module__].__file__))

# Read synset file
with open(config_utils.LABELS, "r") as f:
    synset = literal_eval(f.read())

dlr_model = DLRModel(config_utils.MODEL_DIR, config_utils.DEFAULT_ACCELERATOR)


def enable_camera():
    if platform.machine() == "armv7l":  # RaspBerry Pi
        import picamera

        config_utils.CAMERA = picamera.PiCamera()
    elif platform.machine() == "aarch64":  # Nvidia Jetson TX
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


def predict(image_data):
    r"""
    Performs image classification and predicts using the model.

    :param image_data: numpy array of the resized image passed in for inference.
    """
    PAYLOAD = {}
    PAYLOAD["timestamp"] = str(datetime.now())
    PAYLOAD["inference-type"] = "image-classification"
    PAYLOAD["inference-description"] = "Top {} predictions with score {} or above ".format(
        config_utils.MAX_NO_OF_RESULTS, config_utils.SCORE_THRESHOLD
    )
    PAYLOAD["inference-results"] = []
    try:
        # Run DLR to perform inference with DLC optimized model
        model_output = dlr_model.run(image_data)
        probabilities = model_output[0][0]
        sort_classes_by_probability = argsort(probabilities)[::-1]
        for i in sort_classes_by_probability[: config_utils.MAX_NO_OF_RESULTS]:
            if probabilities[i] >= config_utils.SCORE_THRESHOLD:
                result = {"Label": str(synset[i]), "Score": str(probabilities[i])}
                PAYLOAD["inference-results"].append(result)
        config_utils.logger.info(dumps(PAYLOAD))
        if config_utils.TOPIC.strip() != "":
            ipc_utils.IPCUtils().publish_results_to_cloud(PAYLOAD)
        else:
            config_utils.logger.info("No topic set to publish the inference results to the cloud.")
    except Exception as e:
        config_utils.logger.error("Exception occured during prediction: {}".format(e))


def predict_from_image(image):
    r"""
    Resize the image to the trained model input shape and predict using it.

    :param image: numpy array of the image passed in for inference
    """
    cvimage = resize(image, config_utils.SHAPE)
    predict(cvimage)


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
    elif platform.machine() == "aarch64":  # Nvidia Jetson Nano
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
