#!/bin/bash
echo "=========================================="
echo "Starting Store Intelligence Video Pipeline"
echo "=========================================="

# Run the detection script
python detect.py

echo "=========================================="
echo "Pipeline Complete!"
echo "Events have been saved to events_output.jsonl"
echo "=========================================="