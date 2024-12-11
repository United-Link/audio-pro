#!/bin/bash

LIMIT=${1:-20}

CONFIG_FILE=/root/.config/pipewire/filter-chain.conf.d/filter-chain.conf

sed -i "s/\"Attenuation Limit (dB)\" [0-9]\+$/\"Attenuation Limit (dB)\" $LIMIT/" $CONFIG_FILE

pipewire -c filter-chain.conf

echo "Starting DFN with attenuation limit $LIMIT dB..."