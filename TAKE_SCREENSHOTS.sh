#!/bin/bash
# Screenshot helper script.
# Run this AFTER launching Gazebo and pausing at each waypoint.
# Usage: ./TAKE_SCREENSHOTS.sh A3   (takes screenshot named A3_gz_home.png)

APPROACH=$1
NAME=$2

if [ -z "$APPROACH" ] || [ -z "$NAME" ]; then
    echo "Usage: ./TAKE_SCREENSHOTS.sh <A|B> <label>"
    echo "Examples:"
    echo "  ./TAKE_SCREENSHOTS.sh A A1_rqt_sliders"
    echo "  ./TAKE_SCREENSHOTS.sh A A3_gz_home"
    echo "  ./TAKE_SCREENSHOTS.sh B B2_gz_pre_grasp"
    exit 1
fi

OUTDIR="$(dirname "$0")/approaches/approach_${APPROACH}/screenshots"
OUTFILE="${OUTDIR}/${NAME}.png"

echo "Capturing in 3 seconds... (switch to the correct window)"
sleep 3

scrot "$OUTFILE"
echo "Saved: $OUTFILE"
