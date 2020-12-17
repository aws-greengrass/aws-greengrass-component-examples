/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.aws.greengrass.mqttbridge;

import software.amazon.awssdk.aws.greengrass.GreengrassCoreIPC;
import software.amazon.awssdk.aws.greengrass.GreengrassCoreIPCClient;
import software.amazon.awssdk.aws.greengrass.model.ReportedLifecycleState;
import software.amazon.awssdk.eventstreamrpc.EventStreamRPCConnection;

import java.io.IOException;

public class Main {
    private static EventStreamRPCConnection connection;
    private static GreengrassCoreIPC client;
    private static Worker worker;

    /**
     * Run.
     * @param args arguments
     */
    public static void main(String[] args) {
        try {
            connection = IPCUtil.getEventStreamRpcConnection();
            client = new GreengrassCoreIPCClient(connection);

            worker = new Worker(client);
            worker.startup();
            IPCUtil.reportState(client, ReportedLifecycleState.RUNNING);
            worker.run();
        } catch (Throwable e) {
            e.printStackTrace();
            System.exit(1);
        } finally {
            if (connection != null) {
                connection.close();
            }
            if (worker != null) {
                try {
                    worker.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
