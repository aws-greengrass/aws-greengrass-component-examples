# Deploying Examples to Greengrass

> **Note:** All deployment steps can be performed through the AWS Console. The
> following are CLI instructions.

Detailed deployment documentation can be found here:

- [Getting started guide (console)](https://docs.aws.amazon.com/greengrass/v2/developerguide/deploy-first-component.html)
- [Developer Guide (CLI)](https://docs.aws.amazon.com/greengrass/v2/developerguide/create-deployments.html)

## Prerequisites

- AWS CLI configured with appropriate credentials
- S3 bucket for component artifacts
- Greengrass thing group

## Deployment Steps

### 1. Upload Sample Binary to S3

```bash
aws s3 cp <example>/sample_<name> s3://YOUR_BUCKET/ggl-sdk-samples/sample_<name>
```

### 2. Update Recipe with S3 Location

Copy the sample's `.yml` and update the artifact URI:

```bash
cd <sample_name>
cp <recipe>.yml recipe-deploy.yml
# Edit recipe-deploy.yml and replace:
# URI: s3://EXAMPLE_BUCKET/sample_<name>
# with:
# URI: s3://YOUR_BUCKET/ggl-sdk-samples/sample_<name>
```

### 3. Create Component Version

```bash
aws greengrassv2 create-component-version \
  --inline-recipe file://recipe-deploy.yml \
  --region YOUR_REGION
```

### 4. Deploy to Thing Group

```bash
aws greengrassv2 create-deployment \
  --target-arn "arn:aws:iot:YOUR_REGION:ACCOUNT_ID:thinggroup/YOUR_THING_GROUP" \
  --deployment-name "SampleDeployment" \
  --components '{
    "COMPONENT_NAME": {
      "componentVersion": "VERSION"
    }
  }' \
  --region YOUR_REGION
```
