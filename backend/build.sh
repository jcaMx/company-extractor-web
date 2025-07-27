#!/usr/bin/env bash

# Install Chrome and dependencies for Render
echo "Installing Chrome and dependencies..."

# Update package list
apt-get update

# Install required packages
apt-get install -y wget gnupg unzip

# Add Google Chrome repository
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Update and install Chrome
apt-get update
apt-get install -y google-chrome-stable

# Verify Chrome installation
google-chrome --version

echo "Chrome installation completed!" 