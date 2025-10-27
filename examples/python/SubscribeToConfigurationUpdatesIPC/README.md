# com.example.ConfigSubscriber

This an example component that show how to utilize the greengrass's
subscribe_to_configuration_update IPC command using python's sdk.

## Usage

The component subscribe's to it's own configuration changes so any changes to
it's configuration will lead to a update event trigger.

After deploying the component, you can update its configuration to trigger the
subscription callback.

**Using AWS Console:**

1. Navigate to AWS IoT Greengrass console
2. Select `Deployments` and find the deployment targeting your thing group
3. Click `Actions` > `Revise` > `Next` > `Next`
4. Find `com.example.ConfigSubscriber` in the component list
5. Click `Configure component`
6. Under `Configuration to merge`, add:
   ```json
   {
     "test_str": "updated_value"
   }
   ```
7. Click `Confirm` > `Next` > `Deploy`

**Using AWS CLI:**

```bash
aws greengrassv2 create-deployment \
  --target-arn "arn:aws:iot:REGION:ACCOUNT_ID:thinggroup/YOUR_THING_GROUP" \
  --components '{
    "com.example.ConfigSubscriber": {
      "componentVersion": "VERSION",
      "configurationUpdate": {
        "merge": "{\"test_str\":\"updated_value\"}"
      }
    }
  }' \
  --region YOUR_REGION
```
