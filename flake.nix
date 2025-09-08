# aws-greengrass-lite - AWS IoT Greengrass runtime for constrained devices
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

{
  description = "AWS IoT Greengrass runtime for constrained devices.";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flakelight.url = "github:nix-community/flakelight";
  };
  outputs = { flakelight, ... }@inputs: flakelight ./. ({ lib, ... }: {
    systems = lib.systems.flakeExposed;
    inherit inputs;

    devShell.packages = pkgs: with pkgs; [
      clang-tools
      cmake
      git
    ];

    formatters = { llvmPackages, cmake-format, nodePackages, yapf, ... }:
      let
        fmt-c = "${llvmPackages.clang-unwrapped}/bin/clang-format -i";
        fmt-cmake = "${cmake-format}/bin/cmake-format -i";
        fmt-yaml =
          "${nodePackages.prettier}/bin/prettier --write --parser yaml";
        fmt-md = "${nodePackages.prettier}/bin/prettier --write --parser markdown";
      in
      {
        "*.c" = fmt-c;
        "*.h" = fmt-c;
        "*.cpp" = fmt-c;
        "*.hpp" = fmt-c;
        "CMakeLists.txt" = fmt-cmake;
        ".clang*" = fmt-yaml;
        "*.py" = "${yapf}/bin/yapf -i";
        "*.md" = fmt-md;
      };

    checks.spelling = pkgs: ''
      ${pkgs.nodePackages.cspell}/bin/cspell "**" --quiet
      ${pkgs.coreutils}/bin/sort -cuf misc/dictionary.txt
    '';
  });
}
