# Inference applications using DLR on Windows. 

These example components are used to run sample image classification and object detection inferences.

Image Classification 
 - com.greengrass.DLRImageClassification 
 - com.greengrass.DLRImageClassification.Model

Object Detection
 - com.greengrass.DLRObjectDetection
 - com.greengrass.DLRObjectDetection.Model

### Sample models   

The [releases](https://github.com/aws-greengrass/aws-greengrass-component-examples/releases/) section of this repository provides ML models which can be used as artifacts of the sample model components. These are
pre-trained models from GlounCV Model zoo which are then compiled with AWS SageMaker Neo based on the device type.

Our samples use pre-trained resnet50_v1 model to perform Image Classification and pre-trained yolo3_darknet53_voc to perform Object Detection. 

Use sample models from the releases section based on the inference and device architecture. Example: To run image-classification inference on an windows device, use `DLR-resnet50-win-ImageClassification.zip` as a model artifact in the `com.greengrass.DLRImageClassification.Model` recipe for windows support.

Instructions on how to compile the models from the AWS console can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/neo-job-compilation-console.html) and package the compiled models can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/edge-packaging-job-console.html)

---
### Component configuration
These sample components provide the following configuration parameters that can be customized at the time of deployment. 

**Runtime components**
`com.greengrass.DLR` component installs DLR runtime and other python libraries like awsiotsdk, opencv-python and numpy as the component user directly on the device. 

**Inference components**

The following configuration is applicable for both the `com.greengrass.DLRImageClassification` and 
`com.greengrass.DLRObjectDetection` inference components. 

- **accessControl** (Optional) : The object that contains the authorization policy that allows the component to publish messages to the default notifications topic.

    Default:
    ```
    "accessControl": {
        "aws.greengrass.ipc.mqttproxy": {
            "com.greengrass.DLR<InferenceType>:mqttproxy:1": {
                "policyDescription": "Allows access to publish via topic lambda/dlr/<inference-type>.",
                "operations": [
                    "aws.greengrass#PublishToIoTCore"
                ],
                "resources": [
                    "ml/dlr/<inference-type>"
                ]
            }
        }
    },
    ```

- **PublishResultsOnTopic** (Optional) : The topic on which you want to publish the inference results. If you modify this value, then you must also modify the value of resources in the accessControl parameter to match your custom topic name.

    Default: `ml/dlr/<inference-type>`

- **ImageDirectory** (Optional) : The path of the folder on the device where inference components read images. You can modify this value to any location on your device to which you have read/write access.

    Default: `/greengrass/v2/packages/artifacts-unarchived/<component-name>/<inference-type>/sample_images`
    
- **ImageName** (Optional) : The name of the image that the inference component uses as an input to a make prediction. The component looks for the image in the folder specified in ImageDirectory. By default, the component uses the sample image in the default image directory. AWS IoT Greengrass supports the following image formats: jpeg, jpg, png, and npy.

    Default: `cat.jpeg`

- **InferenceInterval** (Optional) : The time in seconds between each prediction made by the inference code. The sample inference code runs indefinitely and repeats its predictions at the specified time interval. For example, you can change this to a shorter interval if you want to use images taken by a camera for real-time prediction.

    Default: `3600`


## Create components

Follow the steps in order to prepare the component artifacts, recipes and create components. 

1. Go to the terminal and configure your aws credentials as shown below:
    ```
    export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
    export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```
2. After cloning this github repo, navigate to the `machine-learning/dlr-inference/` folder to run the python script `create_components.py` which takes in the following arguments


        -r or --region : Region where you want to create and use the greengrass components (Default: us-east-1).
        -b or --bucket : (Required) Name of the bucket which is used to store the component artifacts.
        -i or --inferenceType : Type of the inference. Values: ImageClassification / ObjectDetection. Creates both inference and model components of that inference type.
        -c or --componentName : Name of the component to create. This will create only one component at a time.     

        Note: 
        1. Bucket name is mandatory. 
        2. inferenceType and componentName args are mutually exclusive. 
       

    Run the following commands in order to create runtime, model and inference lambda components to perform ImageClassification

    1.  Create the runtime component 

        `python3 create_components.py -c com.greengrass.DLR -b bucketName`

    2.  Create the model component (ImageClassification)

        `python3 create_components.py -c com.greengrass.DLRImageClassification.Model -b bucketName` 

    3.  Create the inference component (ImageClassification)

        `python3 create_components.py -c com.greengrass.DLRImageClassification -b bucketName` 


    - This script creates a build folder with the prepared artifacts and upload them to the s3 bucket. The sample models are downloaded from the releases section based on the parameters inference type. This might take several minutes as the artifacts are prepared and uploaded to the desired S3 bucket. .

    - Recipe files are updated with the latest patch version of the component(if the component exists already). Artifact URIs in the recipes are also updated based on the region and bucket parameters.

    - New versions of all the five components are created using the uploaded artifacts and updated recipes. You can find these under My components in your AWS IoT Greengrass console.

## Deploy components

Follow the [documentation]() to deploy inference and model components and run inference on the edge using DLR on windows. 