# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

#!/bin/bash
. $(dirname "$0")/utils.sh

set -eux

kernel=$(uname -s)
dlr_version="1.6.0"
min_py_version="3.0.0"
dlr_directory="neo-ai-dlr"
min_kernel_version="4.9.9"
min_pip_version="20.2.4"
machine=$(uname -m)
python_version=$(echo $(python3 --version) | cut -d' ' -f 2)
pip3_version=$(echo $(pip3 --version) | cut -d' ' -f 2)
jetson_device_chip="/sys/module/tegra_fuse/parameters/tegra_chip_id"
# Supported dlr pip wheels for different devices and dlr versions can be fount at
# https://github.com/neo-ai/neo-ai-dlr/releases
dlr_link="https://neo-ai-dlr-release.s3-us-west-2.amazonaws.com/v"$dlr_version

case "$kernel" in
"Linux")
    if check_dlr "$machine"; then
        echo "Skipping DLR installation as it already exists."
    else
        if is_debian; then
            if [[ "$machine" == "x86_64" ]]; then
                install_python3_libraries
                echo "Installing DLR..."
                pip3 install dlr=="$dlr_version" --user
            elif [[ "$machine" == "armv7l" ]]; then
                install_python3_libraries
                echo "Installing DLR..."
                pip3 install $dlr_link"/rasp3b/dlr-"$dlr_version"-py3-none-any.whl" --user
            elif [[ "$machine" == "aarch64" ]]; then
                install_python3_libraries
                if [ -f "$jetson_device_chip" ]; then
                    echo "Installing DLR..."
                    pip3 install $dlr_link"/jetpack4.4/dlr-"$dlr_version"-py3-none-any.whl" --user
                else
                    echo "Installing DLR..."
                    pip3 install $dlr_link"/rasp4b/dlr-"$dlr_version"-py3-none-any.whl" --user
                fi
            fi
        elif is_centos; then
            if [[ "$machine" == "x86_64" ]]; then
                install_python3_libraries
                echo "Installing DLR..."
                pip3 install dlr=="$dlr_version" --user
            fi
        fi
    fi
    ;;
"Darwin")
    if check_dlr "$machine"; then
        echo "Skipping DLR installation as it already exists."
    else
        install_python3_libraries
        echo "Installing DLR..."
        pip3 install dlr=="$dlr_version" --user
    fi
    ;;
esac
