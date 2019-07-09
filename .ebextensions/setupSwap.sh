#!/bin/bash

SWAPFILE=/var/swapfile
SWAP_MEGABYTES=2048

if [ -f $SWAPFILE ]; then
    echo "Swapfile $SWAPFILE found, already configured"
    exit;
fi

dd if=/dev/zero of=$SWAPFILE bs=1M count=$SWAP_MEGABYTES
chmod 600 $SWAPFILE
mkswap $SWAPFILE
swapon $SWAPFILE