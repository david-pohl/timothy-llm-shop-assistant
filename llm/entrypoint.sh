#!/bin/bash


/bin/ollama serve &

pid=$!

sleep 5

echo "Retrieving LLAMA3.2:1b model..."
ollama pull llama3.2:1b
echo "Done!"

wait $pid
