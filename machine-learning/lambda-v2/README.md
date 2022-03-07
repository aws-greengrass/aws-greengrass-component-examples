# Inference applications that run AWS Lambda functions in a Greengrass V2 component 

These example components are used to run sample image classification and object detection inferences with AWS lambda.


Image Classification 
 - com.lambda.DLRImageClassification (No container mode)
 - com.lambda.Container.DLRImageClassification (Greengrass container mode)
 - com.lambda.DLRImageClassification.Model

Object Detection
 - com.lambda.DLRObjectDetection (No container mode)
 - com.lambda.Container.DLRObjectDetection (Greengrass container mode)
 - com.lambda.DLRObjectDetection.Model

Runtime component 
- com.lambda.DLR 

### Sample models   

The [releases](https://github.com/aws-greengrass/aws-greengrass-component-examples/releases/) section of this repository provides ML models which can be used as artifacts of the sample model components. These are
pre-trained models from GlounCV Model zoo which are then compiled with AWS SageMaker Neo.

Our samples use pre-trained resnet50_v1 model to perform Image Classification and pre-trained yolo3_darknet53_voc to perform Object Detection. 

Download these sample models based on the inference. Example: To run image-classification inference on an aarch64 device, use `DLR-resnet50-aarch64-ImageClassification.tar.gz` as a model artifact in the `com.lambda.DLRImageClassification.Model` recipe for aarch64 support.

Instructions on how to compile the models from the AWS console can be found [here](https://docs.aws.amazon.com/sagemaker/latest/dg/neo-job-compilation-console.html).

---
### Component configuration
These sample components provide the following configuration parameters that can be customized at the time of deployment. 

**Runtime components**
`com.lambda.DLR` component installs DLR runtime and other python libraries like awsiotsdk, opencv-python and numpy as the component user directly on the device. 

**Inference components**

The following configuration is applicable for both the `com.lambda.DLRImageClassification` and 
`com.lambda.DLRObjectDetection` inference components. 

The com.lambda.DLRImageClassification and com.lambda.DLRObjectDetection inference components require the following configuration parameters. You specify these configuration values when you deploy the components. Because these component are Lambda function components, you can't set default configuration values in the component recipe. For more information, see [Update component configurations](https://docs.aws.amazon.com/greengrass/v2/developerguide/update-component-configurations.html).

- **accessControl** (Optional) : The authorization policy that allows the component to publish MQTT messages to AWS IoT Core on the default notifications topic.

    Example:
    ```
    "accessControl": {
        "aws.greengrass.ipc.mqttproxy": {
            "com.lambda.DLR<InferenceType>:mqttproxy:1": {
                "policyDescription": "Allows access to publish via topic lambda/dlr/<inference-type>.",
                "operations": [
                    "aws.greengrass#PublishToIoTCore"
                ],
                "resources": [
                    "lambda/dlr/<inference-type>"
                ]
            }
        }
    },
    ```

- **PublishResultsOnTopic** (Optional) : The MQTT topic where this component publishes inference results. When you modify this value, you must also update the resource value in the `accessControl` parameter to allow this component to publish on this topic.

    Example: `lambda/dlr/<inference-type>`

- **ImageDirectory** (Optional) : The path of the folder on the device where this component reads images. The system user that runs these ML inference components must have read/write access to the folder that you specify.

    Default: `<greengrass-root>/packages/artifacts-unarchived/<component-name>/<inference-type>/sample_images`
    
- **ImageName** (Optional) : The name of the image that the inference component uses as an input to a make prediction. The component looks for the image in the folder specified in ImageDirectory. By default, the component uses the sample image in the default image directory. AWS IoT Greengrass supports the following image formats: jpeg, jpg, png, and npy.

    Default: `cat.jpeg`

- **InferenceInterval** (Optional) : The time in seconds between each prediction made by the inference code. The sample inference code runs indefinitely and repeats its predictions at the specified time interval. For example, you can change this to a shorter interval if you want to use images taken by a camera for real-time prediction.

    Default: `3600`

**Model components**

The following configuration is applicable for both the `com.lambda.DLRObjectDetection.Model` and the `com.lambda.DLRImageClassification.Model` model components.

- **ModelPath** (Optional) : The path of the folder where the packaged model artifacts are unarchived. 

    Default: `<greengrass-root>/work/<component-name>/`


## Create components

Follow the steps in order to prepare the component artifacts, recipes and create components. 

1. Go to the terminal and configure your aws credentials as shown below:
    ```
    export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
    export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```
2. After cloning this GitHub repo, navigate to the `machine-learning/lambda-v2/` folder to run the python script `create_components.py` which takes in the following arguments


        -r or --region : Region where you want to create and use the greengrass components (Example: us-east-1).
        -b or --bucket : (Required) Name of the bucket which is used to store the component artifacts.
        -i or --inferenceType : Type of the inference. Values: ImageClassification / ObjectDetection. Creates both inference and model components of that inference type.
        -c or --componentName : Name of the component to create. This will create only one component at a time.
        -l or --lambdaRole : IAM role attached to the inference lambdas as the lambda execution role.
        -m or --containerMode : Set to 'true' to create lambda components that run inside container.      

        Note: 
        1. Bucket name is mandatory. 
        2. inferenceType and componentName args are mutually exclusive. 
        3. Creation of lambda components require '--lambdaRole' or '-l' argument and the role needs to have trusted entity AWS Service: lambda. 
       

    Run the following commands in order to create runtime, model and inference lambda components to perform ImageClassification

    1.  Create the runtime component 

        `python3 create_components.py -c com.lambda.DLR -b bucketName`

    2.  Create the model component (ImageClassification)

        `python3 create_components.py -c com.lambda.DLRImageClassification.Model -b bucketName` 

    3.  Create the lambda inference component (ImageClassification)

        `python3 create_components.py -c com.lambda.DLRImageClassification -l <lambda-execution-role> -b bucketName` 


    - This script creates a build folder with the prepared artifacts and upload them to the s3 bucket. The sample models are downloaded from the releases section based on the parameters inference type. This might take several minutes as the artifacts are prepared and uploaded to the desired S3 bucket. 

    - This script also creates AWS lambda functions with the inference code and generates greengrass lambda components from the lambda fuctions.

    - Recipe files are updated with the latest patch version of the component(if the component exists already). Artifact URIs in the recipes are also updated based on the region and bucket parameters.

    - New versions of all the five components are created using the uploaded artifacts and updated recipes. You can find these under <b>My components</b> in the AWS IoT Greengrass console.

