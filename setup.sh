#!/bin/bash

# Update the package list and install FFmpeg
apt-get update
apt-get install -y ffmpeg

# Optional: Configure Streamlit settings (headless mode, disable CORS)
mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"iamabdulsamad2.0@gmail.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
