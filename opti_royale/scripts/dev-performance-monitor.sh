#!/bin/bash

# 📊 Development Performance Monitor
# Real-time tracking of development environment resources

echo "🔍 OptiRoyale Development Performance Monitor"
echo "============================================="

# Function to get memory usage in human readable format
get_memory_usage() {
    local mem_total=$(free -h | awk '/^Mem:/ {print $2}')
    local mem_used=$(free -h | awk '/^Mem:/ {print $3}')
    local mem_percent=$(free | awk '/^Mem:/ {printf "%.1f", $3/$2 * 100.0}')
    echo "Memory: $mem_used / $mem_total (${mem_percent}%)"
}

# Function to get CPU usage
get_cpu_usage() {
    local cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "CPU Usage: ${cpu_percent}%"
}

# Function to get VS Code process info
get_vscode_performance() {
    echo "📝 VS Code Performance:"
    ps aux | grep -E "(code|node.*code)" | head -5 | while read line; do
        local mem=$(echo $line | awk '{print $4}')
        local cpu=$(echo $line | awk '{print $3}')
        local cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}' | cut -c1-50)
        echo "  Memory: ${mem}% CPU: ${cpu}% - ${cmd}..."
    done
}

# Function to count workspace files
get_file_count() {
    local total_files=$(find /workspaces/opti_royale -type f | wc -l)
    local js_files=$(find /workspaces/opti_royale -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | wc -l)
    local node_modules=$(find /workspaces/opti_royale -name "node_modules" -type d | wc -l)
    echo "📁 Workspace Files:"
    echo "  Total Files: $total_files"
    echo "  JS/TS Files: $js_files"
    echo "  node_modules dirs: $node_modules"
}

# Function to get development server status
get_dev_servers() {
    echo "🌐 Development Servers:"
    local servers=$(netstat -tulpn 2>/dev/null | grep LISTEN | grep -E ":(3000|3001|5000|8000|8080)" | wc -l)
    if [ "$servers" -gt 0 ]; then
        netstat -tulpn 2>/dev/null | grep LISTEN | grep -E ":(3000|3001|5000|8000|8080)" | while read line; do
            local port=$(echo $line | awk '{print $4}' | cut -d':' -f2)
            echo "  Port $port: Active"
        done
    else
        echo "  No development servers running"
    fi
}

# Function to assess performance health
assess_performance() {
    local mem_percent=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100.0}')
    local cpu_percent=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    
    echo "⚡ Performance Health:"
    
    if [ "$mem_percent" -lt 70 ]; then
        echo "  Memory: ✅ Good ($mem_percent%)"
    elif [ "$mem_percent" -lt 85 ]; then
        echo "  Memory: ⚠️  Warning ($mem_percent%)"
    else
        echo "  Memory: 🚨 Critical ($mem_percent%) - Consider cleanup"
    fi
    
    if (( $(echo "$cpu_percent < 50" | bc -l) )); then
        echo "  CPU: ✅ Good ($cpu_percent%)"
    elif (( $(echo "$cpu_percent < 80" | bc -l) )); then
        echo "  CPU: ⚠️  Warning ($cpu_percent%)"
    else
        echo "  CPU: 🚨 High Load ($cpu_percent%)"
    fi
}

# Function to provide recommendations
provide_recommendations() {
    local mem_percent=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100.0}')
    local file_count=$(find /workspaces/opti_royale -type f | wc -l)
    
    echo "💡 Recommendations:"
    
    if [ "$mem_percent" -gt 80 ]; then
        echo "  🔧 Run memory cleanup: ./scripts/dev-cleanup.sh"
    fi
    
    if [ "$file_count" -gt 30000 ]; then
        echo "  📁 Consider workspace splitting for better performance"
    fi
    
    local vscode_count=$(ps aux | grep -c "[c]ode")
    if [ "$vscode_count" -gt 5 ]; then
        echo "  📝 Multiple VS Code instances detected - consider consolidating"
    fi
    
    local node_modules_count=$(find /workspaces/opti_royale -name "node_modules" -type d | wc -l)
    if [ "$node_modules_count" -gt 3 ]; then
        echo "  📦 Multiple node_modules detected - cleanup opportunity"
    fi
}

# Main monitoring function
main() {
    clear
    echo "🕐 $(date)"
    echo ""
    
    get_memory_usage
    get_cpu_usage
    echo ""
    
    get_vscode_performance
    echo ""
    
    get_file_count
    echo ""
    
    get_dev_servers
    echo ""
    
    assess_performance
    echo ""
    
    provide_recommendations
    echo ""
    
    echo "🔄 Refreshing every 30 seconds... (Ctrl+C to stop)"
}

# Check if running in watch mode
if [ "$1" = "--watch" ]; then
    while true; do
        main
        sleep 30
    done
else
    main
fi
