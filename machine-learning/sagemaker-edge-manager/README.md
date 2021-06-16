# Inference applications using SageMaker Edge Manager Agent component. 

These example components are used to run sample image classification and object detection inferences.

Image Classification 
 - com.greengrass.SageMakerEdgeManager.ImageClassification 
 - com.greengrass.SageMakerEdgeManager.ImageClassification.Model

Object Detection
 - com.greengrass.SageMakerEdgeManager.ObjectDetection
 - com.greengrass.SageMakerEdgeManager.ObjectDetection.Model

### Sample models   

The [releases](https://github.com/aws-greengrass/aws-greengrass-component-examples/releases/) section of this repository provides ML models which can be used as artifacts of the sample model components. These are
pre-trained models from GlounCV Model zoo which are then compiled with AWS SageMaker Neo and packaged with AWS SageMaker Edge Packaging job. 

Our samples use pre-trained resnet50_v1 model to perform Image Classification and pre-trained yolo3_darknet53_voc to perform Object Detection. 

Use sample models from the releases section based on the inference, device and region - `gg-sagemakerEdgeManager-{model-name}-{region}-{arch}-1.0.tar.gz`. Example: To run image-classification inference in us-west-2 on an x64 device arch, use `gg-sagemakerEdgeManager-resnet-us-west-2-x64-1.0.tar.gz` as a model artifact in the `com.greengrass.SageMakerEdgeManager.ImageClassification.Model` recipe for amd64/x64 support. 

Instructions on how to compile the models from the AWS console can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/neo-job-compilation-console.html) and package the compiled models can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/edge-packaging-job-console.html)

---
### Component configuration
These sample components provide the following configuration parameters that can be customized at the time of deployment. 

**Inference components**

The following configuration is applicable for both the com.greengrass.SageMakerEdgeManager.ImageClassification and the com.greengrass.SageMakerEdgeManager.ObjectDetection inference components. 

- **accessControl** (Optional) : The object that contains the authorization policy that allows the component to publish messages to the default notifications topic.

    Default:
    ```
    "accessControl": {
        "aws.greengrass.ipc.mqttproxy": {
            "com.greengrass.SageMakerEdgeManager.<InferenceType>:mqttproxy:1": {
                "policyDescription": "Allows access to publish via topic gg/sageMakerEdgeManager/<inference-type>.",
                "operations": [
                    "aws.greengrass#PublishToIoTCore"
                ],
                "resources": [
                    "gg/sageMakerEdgeManager/<inference-type>"
                ]
            }
        }
    },
    ```

- **PublishResultsOnTopic** (Optional) : The topic on which you want to publish the inference results. If you modify this value, then you must also modify the value of resources in the accessControl parameter to match your custom topic name.

    Default: `gg/sageMakerEdgeManager/<inference-type>`

- **ImageDirectory** (Optional) : The path of the folder on the device where inference components read images. You can modify this value to any location on your device to which you have read/write access.

    Default: `/greengrass/v2/packages/artifacts-unarchived/<component-name>/<inference-type>/sample_images`
    
- **ImageName** (Optional) : The name of the image that the inference component uses as an input to a make prediction. The component looks for the image in the folder specified in ImageDirectory. By default, the component uses the sample image in the default image directory. AWS IoT Greengrass supports the following image formats: jpeg, jpg, png, and npy.

    Default: `cat.jpeg`

- **InferenceInterval** (Optional) : The time in seconds between each prediction made by the inference code. The sample inference code runs indefinitely and repeats its predictions at the specified time interval. For example, you can change this to a shorter interval if you want to use images taken by a camera for real-time prediction.

    Default: `3600`

**Model components**

The following configuration is applicable for both the com.greengrass.SageMakerEdgeManager.ImageClassification.Model and the com.greengrass.SageMakerEdgeManager.ObjectDetection.Model model components.

- **ModelPath** (Optional) : The path of the folder where the packaged model artifacts are unarchived. 

    Default: `/greengrass/v2/work/<component-name>/`


## Create components
Follow the steps in order to prepare the component artifacts, recipes and create components. 

1. Go to the terminal and configure your aws credentials as shown below:
    ```
    export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
    export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```
2. After cloning this github repo, navigate to the `machine-learning/sagemaker-edge-manager/` folder. 

    - Run `create_components.py` as shown below or with the optional arguments. 

        `python3 create_components.py -i ImageClassification` 

        The above command uses **us-east-1**(default) region to create **Image Classification** example components and **ggv2-example-component-artifacts-us-east-1**(default) bucket to store the component artifacts. 
    
    
    - To specify desired region, bucket and inference type, use the following command (region name is appended to the bucket name) 

        `python3 create_components.py -r region -b bucket -i inferenceType`

    - To create a specific component, provide the script with the name of the component using `componentName` argument as shown below. 

        `python3 create_components.py -c componentName` 

        ```
        region - Region where you want to create and use the greengrass components.
        bucket - Name of the bucket which is used to store the component artifacts.
        inferenceType - Type of the inference. Values: ImageClassification / ObjectDetection. 
        componentType - Name of the component to create.

        Note: Inference type and component type args are mutually exclusive. 
        ```
    - This script creates a build folder with the prepared artifacts and upload them to the s3 bucket. The sample models are downloaded from the releases section based on the parameters like region and inference type. This might take several minutes as the artifacts are prepared and uploaded to the desired S3 bucket. 

    - Recipe files are updated with the latest patch version of the component(if the component exists already). Artifact URIs in the recipes are also updated based on the region and bucket parameters.

    - New versions of all the four components are created using the uploaded artifacts and updated recipes. You can find these under My components in your AWS IoT Greengrass console.

## Deploy components

Follow the [documentation](https://docs.aws.amazon.com/greengrass/v2/developerguide/get-started-with-edge-manager-on-greengrass.html#run-sample-sme-image-classification-inference) to deploy inference and model components and run inference on the edge using sagemaker edge manager. 