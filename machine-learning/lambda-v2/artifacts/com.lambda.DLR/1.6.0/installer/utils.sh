# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

get_dlr_version_command=$(
    cat <<END
try:
    import dlr
    print(dlr.__version__)
except Exception as e:
    print(e)
END
)
get_opencv_version_command=$(
    cat <<END
try:
    import cv2
    print(cv2.__version__)
except Exception as e:
    print(e)
END
)
get_numpy_version_command=$(
    cat <<END
try:
    import numpy as np
    print(np.__version__)
except Exception as e:
    print(e)
END
)
get_awsiotsdk_command=$(
    cat <<END
try:
    import awsiot
except Exception as e:
    print(e)
END
)
# disable metrics data collection feature of amazon (DLR version >= 1.4.0)
disable_metric_collection_command=$(
    cat <<END
try:
    import dlr
    version = dlr.__version__
    if int(version.replace(".","")) >= 140 :
        from dlr.counter.phone_home import PhoneHome
        PhoneHome.disable_feature()
except Exception as e:
    print(e)
END
)
version() {
    echo "$@" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }'
}

check_dlr() {
    disable_metric_collection_command
    get_dlr_version=$(python3 -c "$get_dlr_version_command")
    if [[ "$get_dlr_version" == "$dlr_version" ]]; then
        return 0
    else
        return 1
    fi
}
make_and_install() {
    make -j"$(($(nproc) + 1))"
    cd ../python
    python3 setup.py install
}
remove_cloned_directory() {
    current_path=$(dirname $(realpath $0))
    if [[ "$current_path" == *"$dlr_directory"* ]]; then
        arr=(${current_path//"$dlr_directory"/ })
        sudo rm -rf ${arr[0]}"$dlr_directory"
    else
        sudo rm -rf "$dlr_directory"
    fi
}
is_debian() {
    debian=$(apt-get -v &>/dev/null && echo "apt-get")
    if [[ "$debian" == "apt-get" ]]; then
        echo "I am debian"
        return 0
    else
        return 1
    fi
}
is_centos() {
    centos_yum=$(type yum &>/dev/null && echo "yum")
    if [[ "$centos_yum" == "yum" ]]; then
        return 0
    else
        return 1
    fi
}

##############  Common  ####################
# Install python3 libraries.
install_python3_libraries() {
    # Check if opencv already exists on the machine. Otherwise, install it.
    opencv=$(python3 -c "$get_opencv_version_command")
    if [[ "$opencv" == *"No module named 'cv2'"* ]]; then
        echo "Installing opencv..."
        pip3 install opencv-python --user
    else
        echo "Skipping opencv installation as it already exists."
    fi
    # Check if numpy already exists on the machine. Otherwise, install it.
    numpy=$(python3 -c "$get_numpy_version_command")
    if [[ "$numpy" == *"No module named 'numpy'"* ]]; then
        echo "Installing numpy..."
        pip3 install numpy --user
    else
        echo "Skipping numpy installation as it already exists."
    fi
    # Check if awsiotsdk already exists on the machine. Otherwise, install it.
    awsiotsdk=$(python3 -c "$get_awsiotsdk_command")
    if [[ "$awsiotsdk" == *"No module named 'awsiot'"* ]]; then
        echo "Installing awsiotsdk..."
        pip3 install awsiotsdk --user
    else
        echo "Skipping awsiotsdk installation as it already exists."
    fi
}
