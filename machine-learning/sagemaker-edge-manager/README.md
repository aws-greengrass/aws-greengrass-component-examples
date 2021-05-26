## Inference applications using SageMaker Edge Manager Agent component. 

These example components are used to run sample image classification and object detection inferences.

Image Classification 
 - com.greengrass.SageMakerEdgeManager.ImageClassification 
 - com.greengrass.SageMakerEdgeManager.ImageClassification.Model

Object Detection
 - com.greengrass.SageMakerEdgeManager.ObjectDetection
 - com.greengrass.SageMakerEdgeManager.ObjectDetection.Model

### Create components.
Follow the steps in order to prepare the component artifacts, recipes and create components. 

1. Go to the terminal and configure your aws credentials as shown below:
```
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
2. After cloning this github repo, navigate to the `machine-learning/sagemaker-edge-manager/` folder. 
Run `create_components.py` as shown below or with the optional arguments. 

    `python3 create_components.py` 

    The above command by default uses **us-east-1** region to create the components and  **ggv2-example-component-artifacts** bucket to store the component artifacts . 

    To specify desired region and bucket, use the following command 

    `python3 create_components.py -r region -b bucket`
    ```
    region - Region where you want to create and use the greengrass components.
    bucket - Name of the bucket which is used to store the component artifacts.
    ```

    This script creates a build folder with the prepared artifacts and upload them to the s3 bucket. Model artifacts are copied directly from the public s3 location to the desired s3 bucket. 

    Recipe files are updated with the latest patch version of the component(if the component exists already). Artifact URIs in the recipes are also updated based on the region and bucket parameters.

    New versions of all the four components are created using the uploaded artifacts and updated recipes. You can find these under My components in your AWS IoT Greengrass console.

### Deploy components

Follow the documentation at [Link](Link-to-the-documentation) to deploy the inference and model components to run the inference. 



