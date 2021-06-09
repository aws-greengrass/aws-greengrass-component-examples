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
        if component.startswith(".") and inferenceType not in component:
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


def download_model(build, models):
    for model in models:
        model_url = "{}/{}".format(model_releases, model)
        local_artifact = "{}/{}".format(build, model)
        urllib.request.urlretrieve(model_url, local_artifact)
        rel_path = os.path.relpath(local_artifact, build_dir_path)
        upload_artifacts(local_artifact, rel_path)


def create_recipes():
    os.makedirs(build_recipes_path, mode=0o777, exist_ok=True)
    for component_recipe in os.listdir(recipes_path):
        with open(
            os.path.join(recipes_path, component_recipe),
        ) as f:
            recipe = f.read()
        component = component_recipe.split("-")
        c_name = component[0]
        c_version = component[1].split(".json")[0]
        latest_version = get_latest_version(c_name, c_version)
        recipe = recipe.replace("$BUCKETNAME$", bucket)
        recipe = recipe.replace("$REGION$", region)
        recipe = recipe.replace("$COMPONENT_VERSION$", latest_version)
        recipe = json.loads(recipe)
        recipe["ComponentVersion"] = latest_version
        recipe_file_name = "{}-{}.json".format(c_name, recipe["ComponentVersion"])
        with open(os.path.join(build_recipes_path, recipe_file_name), "w") as f:
            f.write(json.dumps(recipe, indent=4))


def get_latest_version(c_name, c_version):
    try:
        account = get_account_number()
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
        response = s3_client.upload_file(file_name, bucket, object_name)
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
                response = greengrass_client.create_component_version(inlineRecipe=f.read())
            except Exception as e:
                print(
                    "Failed to create the component using the recipe at {}.\nException: {}".format(
                        recipe_file_path, e
                    )
                )
                exit(1)


def get_account_number():
    try:
        response = sts_client.get_caller_identity()
        if response is not None:
            account = response["Account"]
            return account
    except Exception as e:
        print("Cannot get the account id from the credentials.\nException: {}".format(e))
        exit(1)


dir_path = os.path.dirname(os.path.realpath(__file__))
artifacts_path = os.path.join(dir_path, "artifacts")
recipes_path = os.path.join(dir_path, "recipes")
build_dir_path = os.path.join(dir_path, "build")
build_artifacts_path = os.path.join(build_dir_path, "artifacts")
build_recipes_path = os.path.join(build_dir_path, "recipes")

shutil.rmtree(build_dir_path, ignore_errors=True, onerror=None)

region = "us-east-1"
bucket = "ggv2-example-component-artifacts"
inferenceType = ""
model_releases = "https://github.com/aws-greengrass/aws-greengrass-component-examples/releases/download/v1.0"

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--region",
    "-r",
    default=region,
    help="Greengrass components will be created in the region.",
)
parser.add_argument(
    "--bucket",
    "-b",
    default=bucket,
    help="This bucket will be used to store the component artifacts.",
)
parser.add_argument(
    "--inference",
    "-i",
    default=inferenceType,
    help="This bucket will be used to store the component artifacts.",
)

args = parser.parse_args()

region = args.region
bucket = "{}-{}".format(args.bucket, region)
inference = args.inferenceType

inference_models = {
    "com.greengrass.SageMakerEdgeManager.ImageClassification.Model": [
        "gg-sagemakerEdgeManager-resnet-{}-x64-1.0.tar.gz".format(region),
        "gg-sagemakerEdgeManager-resnet-{}-armv8-1.0.tar.gz".format(region),
    ],
    "com.greengrass.SageMakerEdgeManager.ObjectDetection.Model": [
        "gg-sagemakerEdgeManager-darknet-{}-x64-1.0.tar.gz".format(region),
        "gg-sagemakerEdgeManager-darknet-{}-armv8-1.0.tar.gz".format(region),
    ],
}

greengrass_client = boto3.client("greengrassv2", region_name=region)
if region is None or region == "us-east-1":
    s3_client = boto3.client("s3", region_name=region)
else:
    s3_client = boto3.client("s3")
sts_client = boto3.client("sts")

create_bucket()
create_artifacts()
create_recipes()
create_components()
