/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */

package com.aws.greengrass.mqttbridge;

import lombok.NonNull;
import software.amazon.awssdk.aws.greengrass.GreengrassCoreIPC;
import software.amazon.awssdk.aws.greengrass.model.QOS;
import software.amazon.awssdk.aws.greengrass.model.ReportedLifecycleState;
import software.amazon.awssdk.aws.greengrass.model.UpdateStateRequest;
import software.amazon.awssdk.crt.io.ClientBootstrap;
import software.amazon.awssdk.crt.io.EventLoopGroup;
import software.amazon.awssdk.crt.io.SocketOptions;
import software.amazon.awssdk.eventstreamrpc.EventStreamRPCConnection;
import software.amazon.awssdk.eventstreamrpc.EventStreamRPCConnectionConfig;
import software.amazon.awssdk.eventstreamrpc.GreengrassConnectMessageSupplier;

import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;

/**
 * Static utility class for creating an IPC connection to the Greengrass IPC server.
 */
public final class IPCUtil {
    // Meaningless port number. It isn't used for anything, but we need to specify _some_ value.
    public static final int DEFAULT_PORT_NUMBER = 8033;

    private IPCUtil() {
    }

    /**
     * Get a connection to the Greengrass IPC server.
     *
     * @return connection
     * @throws ExecutionException if connecting fails
     * @throws InterruptedException if connecting is interrupted
     */
    public static EventStreamRPCConnection getEventStreamRpcConnection()
            throws ExecutionException, InterruptedException {
        String ipcServerSocketPath = System.getenv("AWS_GG_NUCLEUS_DOMAIN_SOCKET_FILEPATH_FOR_COMPONENT");
        String authToken = System.getenv("SVCUID");
        SocketOptions socketOptions = IPCUtil.getSocketOptionsForIPC();

        return connectToGGCOverEventStreamIPC(socketOptions, authToken, ipcServerSocketPath);
    }

    // removed dependency on kernel, as it is only being used to pull ipcServerSocketPath
    private static EventStreamRPCConnection connectToGGCOverEventStreamIPC(SocketOptions socketOptions,
                                                                           String authToken, String ipcServerSocketPath)
            throws ExecutionException, InterruptedException {

        try (EventLoopGroup elGroup = new EventLoopGroup(1);
             ClientBootstrap clientBootstrap = new ClientBootstrap(elGroup, null)) {

            final EventStreamRPCConnectionConfig config =
                    new EventStreamRPCConnectionConfig(clientBootstrap, elGroup, socketOptions, null,
                            ipcServerSocketPath, DEFAULT_PORT_NUMBER,
                            GreengrassConnectMessageSupplier.connectMessageSupplier(authToken));
            final CompletableFuture<Void> connected = new CompletableFuture<>();
            final EventStreamRPCConnection connection = new EventStreamRPCConnection(config);
            final boolean[] disconnected = {false};
            final int[] disconnectedCode = {-1};
            //this is a bit cumbersome but does not prevent a convenience wrapper from exposing a sync
            //connect() or a connect() that returns a CompletableFuture that errors
            //this could be wrapped by utility methods to provide a more
            connection.connect(new EventStreamRPCConnection.LifecycleHandler() {
                //only called on successful connection.
                // That is full on Connect -> ConnectAck(ConnectionAccepted=true)
                @Override
                public void onConnect() {
                    connected.complete(null);
                }

                @Override
                public void onDisconnect(int errorCode) {
                    disconnected[0] = true;
                    disconnectedCode[0] = errorCode;
                }

                //This on error is for any errors that is connection level, including problems during connect()
                @Override
                public boolean onError(Throwable t) {
                    connected.completeExceptionally(t);
                    return true;    //hints at handler to disconnect due to this error
                }
            });
            connected.get();
            return connection;
        }
    }

    private static SocketOptions getSocketOptionsForIPC() {
        SocketOptions socketOptions = new SocketOptions();
        socketOptions.connectTimeoutMs = 3000;
        socketOptions.domain = SocketOptions.SocketDomain.LOCAL;
        socketOptions.type = SocketOptions.SocketType.STREAM;
        return socketOptions;
    }

    /**
     * Convert qos integer to QOS enum.
     *
     * @param qos qos value.
     * @return QOS enum value.
     */
    public static QOS getQOSFromValue(int qos) {
        if (qos == 1) {
            return QOS.AT_LEAST_ONCE;
        } else if (qos == 0) {
            return QOS.AT_MOST_ONCE;
        }
        return QOS.AT_LEAST_ONCE; //default value
    }

    /**
     * Report a state.
     *
     * @param greengrassCoreIPCClient IPC client
     * @param state new state.
     * @throws ExecutionException if updating fails
     * @throws InterruptedException if updating is interrupted
     */
    public static void reportState(@NonNull GreengrassCoreIPC greengrassCoreIPCClient,
                                   @NonNull ReportedLifecycleState state)
            throws ExecutionException, InterruptedException {
        UpdateStateRequest updateStateRequest = new UpdateStateRequest();
        updateStateRequest.setState(state);
        greengrassCoreIPCClient.updateState(updateStateRequest, Optional.empty()).getResponse().get();
    }
}
