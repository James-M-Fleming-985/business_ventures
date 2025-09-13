#!/bin/bash
# 🚀 Performance Monitor Script
# Real-time monitoring of VS Code environment performance

echo "🔍 OptiRoyale Environment Performance Monitor"
echo "=============================================="
echo "$(date): Starting performance monitoring..."
echo

# Memory Usage
echo "📊 MEMORY USAGE:"
free -h | grep -E "Mem:|Swap:"
echo

# Top Memory Consumers
echo "🔥 TOP MEMORY PROCESSES:"
ps aux --sort=-%mem | head -8 | awk '{printf "%-12s %5s %5s %s\n", $1, $3, $4, $11}' | head -8
echo

# Disk Usage
echo "💾 DISK USAGE:"
df -h | grep -E "overlay|/dev/root"
echo

# TypeScript Server Status
echo "🔧 TYPESCRIPT SERVERS:"
ps aux | grep tsserver | grep -v grep | wc -l | awk '{print "Active TS Servers: " $1}'
ps aux | grep tsserver | grep -v grep | awk '{print "PID: " $2 " Memory: " $4 "% - " $11}' | head -3
echo

# Node.js Processes
echo "⚡ NODE.JS PROCESSES:"
ps aux | grep node | grep -v grep | wc -l | awk '{print "Active Node Processes: " $1}'
echo

# Project Sizes
echo "📁 PROJECT SIZES:"
du -sh /workspaces/opti_royale/node_modules /workspaces/opti_royale/.git /workspaces/opti_royale/*.md 2>/dev/null | sort -hr
echo

echo "✅ Performance monitoring complete - $(date)"
echo "=============================================="
