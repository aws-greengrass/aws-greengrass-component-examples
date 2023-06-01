# Companion code for Managing Per-Device Configuration with an AWS IoT Greengrass Fleet

## Build and Publish
1. Install Greengrass development kit: `pip3 install git+https://github.com/aws-greengrass/aws-greengrass-gdk-cli.git@v1.2.3`
2. Edit bucket and AWS region in gdk-config.json as needed
3. Put AWS credentials into your environment so GDK can upload to S3 and create the Greengrass component
4. NPM install, build, and publish BusinessLogic component into your AWS account.

    ```bash
    cd BusinessLogic && npm i && gdk component build && gdk component publish; cd ..
    ```
