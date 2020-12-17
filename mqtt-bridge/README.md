## AWS Greengrass MQTT Bridge Example

These examples should be taken as a starting point, and not simply deployed as-is.

This component bridges a local MQTT Broker to the AWS IoT Core broker by automatically forwarding
 messages between the device and cloud on specified topics.
 
### Default configuration
```yaml
mappings:
    localTopics:
      - "/localTopic"
    cloudTopics:
      - "/cloudTopic"
connectionInfo:
    brokerUri: "tcp://localhost:1883"
    clientId: "bridger"
    username: null
    password: null
```

## Usage
Using the example recipe `recipe.yaml` create a new component for the MQTT Bridge. Depending on your use case,
you may also want to create a component for the MQTT Broker, one example is provided in `mosquitto.yaml` which works
on Ubuntu. If you create a component for the broker, then you should update the MQTT Bridge component to have a `HARD`
dependency on that component.

When deploying the bridge, make sure to set the configuration with the topics that you wish to forward and the proper
connection information for the running local broker including the URI and username and password (if any).

In this example code, configuration updates will not take effect until the MQTT Bridge component is entirely restarted.


## License

These examples are licensed under the Apache 2.0 License. 
