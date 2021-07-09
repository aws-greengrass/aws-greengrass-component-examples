# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import shutil
import ssl
import urllib.request

import boto3

ssl._create_default_https_context = ssl._create_unverified_context


def create_artifacts():
    for component in os.listdir(artifacts_path):
        if skip_creation(component):
            continue
        component_path = os.path.join(artifacts_path, component)
        for version in os.listdir(component_path):
            if version.startswith("."):
                continue
            version_path = os.path.join(component_path, version)
            component_latest_version = get_latest_version(component, version)
            build = os.path.join(build_artifacts_path, component, component_latest_version)
            os.makedirs(build, mode=0o777, exist_ok=True)
            for file in os.listdir(version_path):
                if file.startswith("."):
                    continue
                file_path = os.path.join(version_path, file)
                build_file = os.path.join(build, file)
                if os.path.isdir(file_path):
                    shutil.make_archive(build_file, "zip", file_path)
                    zip_file = "{}.zip".format(build_file)
                    rel_path = os.path.relpath(zip_file, build_dir_path)
                    upload_artifacts(zip_file, rel_path)
                elif os.path.isfile(file_path):
                    rel_path = os.path.relpath(build_file, build_dir_path)
                    shutil.copy(file_path, build_file)
                    upload_artifacts(build_file, rel_path)
            if ".Model" in component:
                download_model(build, inference_models[component])


def create_lambda_artifacts():
    for component in os.listdir(lambda_artifacts_path):
        if skip_lambda_component_creation(component):
            continue
        component_path = os.path.join(lambda_artifacts_path, component)
        for version in os.listdir(component_path):
            if version.startswith("."):
                continue
            version_path = os.path.join(component_path, version)
            component_latest_version = get_latest_version(component, version)
            build = os.path.join(build_lambda_artifacts_path, component, component_latest_version)
            os.makedirs(build, mode=0o777, exist_ok=True)
            for file in os.listdir(version_path):
                if file.startswith("."):
                    continue
                file_path = os.path.join(version_path, file)
                build_file = os.path.join(build, file)
                if os.path.isdir(file_path):
                    shutil.make_archive(build_file, "zip", file_path)
                    zip_file = "{}.zip".format(build_file)
                    create_lambda(zip_file, component)


def create_lambda(zip_file, component):
    function_name = component.split(".")[-1]
    if lambda_role == "":
        print(
            "Please pass in the lambda execution role required to create the inference lambda as '--lambdaRole' or '-l' argument"
        )
        exit(1)
    with open(zip_file, "rb") as f:
        code = f.read()
    try:
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.8",
            Role="arn:aws:iam::{}:role/{}".format(account, lambda_role),
            Handler="inference.lambda_handler",
            Timeout=123,
            MemorySize=128,
            Publish=True,
            PackageType="Zip",
            Code={"ZipFile": code},
        )
    except Exception as e:
        print(
            "Cannot create function {} as it already exists. Updating the function code instead.".format(
                function_name
            )
        )
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=code,
        )


def download_model(build, models):
    for model in models:
        print("Downloading model {} from the releases section...".format(model))
        model_url = "{}/{}".format(model_releases, model)
        local_artifact = "{}/{}".format(build, model)
        urllib.request.urlretrieve(model_url, local_artifact)
        rel_path = os.path.relpath(local_artifact, build_dir_path)
        upload_artifacts(local_artifact, rel_path)


def create_recipes():
    os.makedirs(build_recipes_path, mode=0o777, exist_ok=True)
    for component_recipe in os.listdir(recipes_path):
        component = component_recipe.split("-")
        c_name = component[0]
        c_version = component[1].split(".json")[0]
        if skip_creation(c_name):
            continue
        latest_version = get_latest_version(c_name, c_version)
        with open(
            os.path.join(recipes_path, component_recipe),
        ) as f:
            recipe = f.read()
        recipe = recipe.replace("$BUCKETNAME$", bucket)
        recipe = recipe.replace("$REGION$", region)
        recipe = recipe.replace("$COMPONENT_VERSION$", latest_version)
        recipe = json.loads(recipe)
        recipe["ComponentVersion"] = latest_version
        recipe_file_name = "{}-{}.json".format(c_name, recipe["ComponentVersion"])
        with open(os.path.join(build_recipes_path, recipe_file_name), "w") as f:
            f.write(json.dumps(recipe, indent=4))


def create_lambda_recipes():
    os.makedirs(build_lambda_recipes_path, mode=0o777, exist_ok=True)
    for component_recipe in os.listdir(lambda_recipes_path):
        component = component_recipe.split("-")
        c_name = component[0]
        c_version = component[1].split(".json")[0]
        if skip_lambda_component_creation(c_name):
            continue
        latest_version = get_latest_version(c_name, c_version)
        with open(
            os.path.join(lambda_recipes_path, component_recipe),
        ) as f:
            recipe = f.read()
        function_name = c_name.split(".")[-1]
        response = lambda_client.publish_version(FunctionName=function_name)
        lambda_arn = response["FunctionArn"]
        recipe = recipe.replace("$LAMBDA_ARN$", lambda_arn)
        recipe = recipe.replace("$COMPONENT_VERSION$", latest_version)
        recipe = json.loads(recipe)
        recipe_file_name = "{}-{}.json".format(c_name, latest_version)
        with open(os.path.join(build_lambda_recipes_path, recipe_file_name), "w") as f:
            f.write(json.dumps(recipe, indent=4))


def get_latest_version(c_name, c_version):
    try:
        print(
            "Fetching the component {} from the account: {}, region: {}".format(
                c_name, account, region
            )
        )
        response = greengrass_client.list_component_versions(
            arn="arn:aws:greengrass:{}:{}:components:{}".format(region, account, c_name),
        )
        if response is not None:
            component_versions = response["componentVersions"]
            if component_versions:
                versions = component_versions[0]["componentVersion"]
                split = versions.split("-")[0].split(".")
                major = split[0]
                minor = split[1]
                patch = split[2]
                return "{}.{}.{}".format(major, minor, str(int(patch) + 1))
            else:
                return c_version
    except Exception as e:
        print("Error getting the latest version of the component.\nException: {}".format(e))


def create_bucket():
    if bucket_exists(bucket):
        print("Bucket:{} already exists.".format(bucket))
        return
    try:
        if region is None or region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket)
        else:
            location = {"LocationConstraint": region}
            s3_client.create_bucket(Bucket=bucket, CreateBucketConfiguration=location)
    except Exception as e:
        print("Failed to create the bucket: {}.\nException: {}".format(bucket, e))
        exit(1)
    print("Successfully created the artifacts bucket {}".format(bucket))


def bucket_exists(bucket_name):
    response = s3_client.list_buckets()
    if response is not None:
        for bucket in response["Buckets"]:
            if bucket["Name"] == bucket_name:
                return True
        return False


def upload_artifacts(file_name, object_name=None):
    if object_name is None:
        object_name = file_name
    try:
        print("Uploading artifacts to the bucket {} with key {}.".format(bucket, object_name))
        s3_client.upload_file(file_name, bucket, object_name)
    except Exception as e:
        print(
            "Failed to upload the artifacts to the bucket {} with key {}.\nException: {}".format(
                bucket, object_name, e
            )
        )
        exit(1)
    print(
        "Successfully uploaded the artifacts to the bucket {} with key {}.".format(
            bucket, object_name
        )
    )


def create_components():
    for component_recipe in os.listdir(build_recipes_path):
        recipe_file_path = os.path.join(build_recipes_path, component_recipe)
        with open(
            recipe_file_path,
        ) as f:
            try:
                greengrass_client.create_component_version(inlineRecipe=f.read())
            except Exception as e:
                print(
                    "Failed to create the component using the recipe at {}.\nException: {}".format(
                        recipe_file_path, e
                    )
                )
                exit(1)
            print("Created component {}".format(component_recipe))


def create_lambda_components():
    for component_recipe in os.listdir(build_lambda_recipes_path):
        recipe_file_path = os.path.join(build_lambda_recipes_path, component_recipe)
        with open(
            recipe_file_path,
        ) as f:
            try:
                greengrass_client.create_component_version(lambdaFunction=json.load(f))
            except Exception as e:
                print(
                    "Failed to create the component using the recipe at {}.\nException: {}".format(
                        recipe_file_path, e
                    )
                )
                exit(1)
            print("Created lambda component {}".format(component_recipe))


def get_account_number():
    try:
        response = sts_client.get_caller_identity()
        if response is not None:
            account = response["Account"]
            return account
    except Exception as e:
        print("Cannot get the account id from the credentials.\nException: {}".format(e))
        exit(1)


def skip_creation(component):
    return (
        (component_argument != "" and component_argument != component)
        or component.startswith(".")
        or inferenceType not in component
    )


def skip_lambda_component_creation(component):
    return skip_creation(component) or (
        containerMode.lower() == "true" and ".Container" not in component
    )


dir_path = os.path.dirname(os.path.realpath(__file__))
artifacts_path = os.path.join(dir_path, "artifacts")
lambda_artifacts_path = os.path.join(dir_path, "lambda-artifacts")
recipes_path = os.path.join(dir_path, "recipes")
lambda_recipes_path = os.path.join(dir_path, "lambda-recipes")
build_dir_path = os.path.join(dir_path, "build")
build_artifacts_path = os.path.join(build_dir_path, "artifacts")
build_lambda_artifacts_path = os.path.join(build_dir_path, "lambda-artifacts")
build_recipes_path = os.path.join(build_dir_path, "recipes")
build_lambda_recipes_path = os.path.join(build_dir_path, "lambda-recipes")

shutil.rmtree(build_dir_path, ignore_errors=True, onerror=None)

region = "us-east-1"
inferenceType = ""
component_argument = ""
model_releases = (
    "https://github.com/aws-greengrass/aws-greengrass-component-examples/releases/download/v1.0"
)

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--region",
    "-r",
    default=region,
    help="Greengrass components will be created in the region.",
)
parser.add_argument(
    "--lambdaRole",
    "-l",
    default="",
    help="Lambda execution role attached to the inference lambda.",
)
parser.add_argument(
    "--containerMode",
    "-m",
    default="",
    help="Specify whether or not the Lambda function runs in a container",
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--inferenceType",
    "-i",
    default=inferenceType,
    help="Components needed for only this type of inference are created.",
)
group.add_argument(
    "--componentName",
    "-c",
    default=component_argument,
    help="Name of the component to be created.",
)
requiredArgs = parser.add_argument_group('Required arguments')
requiredArgs.add_argument(
    "--bucket",
    "-b",
    required=True,
    help="S3 bucket used to store the component artifacts.",
)

args = parser.parse_args()

region = args.region
bucket = args.bucket
lambda_role = args.lambdaRole
inferenceType = args.inferenceType
component_argument = args.componentName
containerMode = args.containerMode

inference_models = {
    "com.lambda.DLRImageClassification.Model": [
        "DLR-resnet50-aarch64-cpu-ImageClassification.tar.gz",
        "DLR-resnet50-x86_64-cpu-ImageClassification.tar.gz",
        "DLR-resnet50-armv7l-cpu-ImageClassification.tar.gz",
    ],
    "com.lambda.DLRObjectDetection.Model": [
        "DLR-yolo3-aarch64-cpu-ObjectDetection.tar.gz",
        "DLR-yolo3-x86_64-cpu-ObjectDetection.tar.gz",
        "DLR-yolo3-armv7l-cpu-ObjectDetection.tar.gz",
    ],
}
lambda_client = boto3.client("lambda", region_name=region)
greengrass_client = boto3.client("greengrassv2", region_name=region)
if region is None or region == "us-east-1":
    s3_client = boto3.client("s3", region_name=region)
else:
    s3_client = boto3.client("s3")
sts_client = boto3.client("sts")
account = get_account_number()

create_bucket()
create_artifacts()
create_lambda_artifacts()
create_recipes()
create_lambda_recipes()
create_components()
create_lambda_components()
