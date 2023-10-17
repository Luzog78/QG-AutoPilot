#!/bin/bash

echo "Launching stable diffusion..."

if [ $# -eq 0 ]
  then
	echo "No arguments supplied"
	exit 1
fi

cd "$1"

shift

./webui.sh $@
