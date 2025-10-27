import time
import datetime
import sys
from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2

sys.stdout = open(sys.stdout.fileno(), 'w', 1)
sys.stderr = open(sys.stderr.fileno(), 'w', 1)


def main():
    print("Starting configuration updater...")
    ipc_client = GreengrassCoreIPCClientV2()

    init_val = 1
    print(f"Initializing counter value to {init_val}")

    try:
        ipc_client.update_configuration(timestamp=datetime.datetime.now(),
                                        value_to_merge={"counter": init_val})
        print("Configuration update successful")
    except Exception as e:
        print(f"Configuration update failed: {type(e).__name__}: {e}")
        return

    while True:
        try:
            config_response = ipc_client.get_configuration(
                component_name="com.example.ConfigUpdater")

            val = (config_response.value or {}).get("counter", init_val)
            print(f"counter value is {val}")

            val += 1
            print(f"Setting counter value to {val}")

            ipc_client.update_configuration(timestamp=datetime.datetime.now(),
                                            value_to_merge={"counter": val})

        except Exception as e:
            print(f"Error in loop: {type(e).__name__}: {e}")
            break

        for i in range(15, 0, -1):
            print(f"Next update in {i} seconds...")
            time.sleep(1)


main()
