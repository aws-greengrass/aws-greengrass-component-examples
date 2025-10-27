import asyncio
import sys
from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2

sys.stdout = open(sys.stdout.fileno(), 'w', 1)
sys.stderr = open(sys.stderr.fileno(), 'w', 1)

counter = 0


def on_stream_event(event):
    global counter
    print(f"Stream event received: {event}")
    print(f"Event type: {type(event)}")
    if hasattr(event, 'configuration_update_event'):
        config_event = event.configuration_update_event
        print("Configuration update received:")
        print(f"  Component: {config_event.component_name}")
        print(f"  Key path: {config_event.key_path}")
        if hasattr(config_event, 'value'):
            print(f"  Value: {config_event.value}")
        counter = 0
    else:
        print(f"Event attributes: {dir(event)}")


def on_stream_error(error):
    print(f"Stream error: {type(error).__name__}: {error}")
    return False


def on_stream_closed():
    print("Stream closed")


async def main():
    try:
        print("Creating IPC client...")
        ipc_client = GreengrassCoreIPCClientV2()
        print("Connected to Greengrass IPC")

        print("Subscribing to configuration updates...")
        response, operation = ipc_client.subscribe_to_configuration_update(
            component_name="com.example.ConfigSubscriber",
            on_stream_event=on_stream_event,
            on_stream_error=on_stream_error,
            on_stream_closed=on_stream_closed)

        print(f"Subscription response: {response}")
        print(f"Operation: {operation}")
        print(
            "Subscribed to com.example.ConfigSubscriber configuration updates. Waiting for updates..."
        )

        global counter
        while True:
            counter += 1
            print(f"Waiting... ({counter})")
            await asyncio.sleep(5)

    except Exception as e:
        print(f"Error in main: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


asyncio.run(main())
