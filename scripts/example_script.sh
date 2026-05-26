#!/bin/bash
# =============================================================
# Example: Start Minecraft server on an Ubuntu host
# Uploaded and executed remotely by VPS Manager.
# =============================================================
SERVER_DIR="/home/ubuntu/minecraft"
JAR="server.jar"
RAM="1024M"

echo "[$(date)] Starting Minecraft server..."
cd "$SERVER_DIR" || { echo "ERROR: $SERVER_DIR not found"; exit 1; }

if [ ! -f "$JAR" ]; then
    echo "ERROR: $JAR not found in $SERVER_DIR"
    exit 1
fi

java -Xmx${RAM} -Xms${RAM} -jar "$JAR" nogui

echo "[$(date)] Server stopped (exit code: $?)"
