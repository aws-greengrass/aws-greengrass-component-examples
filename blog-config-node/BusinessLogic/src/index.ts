/**
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0.
 */

import { greengrasscoreipc } from 'aws-iot-device-sdk-v2';

const CONFIG_COMPONENT = "ConfigHolder";

async function main() {
    try {
        let client = greengrasscoreipc.createClient();

        await client.connect();

        const config = await client.getConfiguration({ componentName: CONFIG_COMPONENT, keyPath: [] });
        console.log("Got initial config", JSON.stringify(config.value));
        console.log("Subscribing to config changes");

        // Setup subscription handle
        const subscription_handle = client.subscribeToConfigurationUpdate({ componentName: CONFIG_COMPONENT, keyPath: [] });
        // Setup listener for config change events
        subscription_handle.on("message", async (event) => {
            console.log("Config changed, will pull full new config immediately", JSON.stringify(event.configurationUpdateEvent?.keyPath));

            const config = await client.getConfiguration({ componentName: CONFIG_COMPONENT, keyPath: [] });
            console.log("Got new full config", JSON.stringify(config.value));
        });

        // Perform the subscription
        await subscription_handle.activate();
        console.log("Subscribed to config changes");
    } catch (err) {
        console.log("Aw shucks: ", err);
    }
}

main();
