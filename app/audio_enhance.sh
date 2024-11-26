#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <attenuation_limit>"
    exit 1
fi

LIMIT=$1

CONFIG_FILE=/root/.config/pipewire/filter-chain.conf.d/filter-chain.conf

sed -i "s/\"Attenuation Limit (dB)\" 0/\"Attenuation Limit (dB)\" $LIMIT/" $CONFIG_FILE

pipewire -c filter-chain.conf

echo "Starting DFN with attenuation limit $LIMIT dB..."