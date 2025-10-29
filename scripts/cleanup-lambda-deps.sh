#!/bin/bash
set -e

echo "🧹 Cleaning up Lambda dependencies..."

cd "$(dirname "$0")/../lambda"

# Show current disk usage
echo "📊 Current disk usage:"
du -sh . 2>/dev/null || echo "Unable to calculate"

# Remove old packages
echo ""
echo "🗑️  Removing old packages..."
rm -rf package/ *.zip 2>/dev/null || true

# Clean pip cache
echo "🧼 Cleaning pip cache..."
pip3 cache purge 2>/dev/null || true

# Remove __pycache__
echo "🗑️  Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Show new disk usage
echo ""
echo "✅ Cleanup complete!"
echo "📊 New disk usage:"
du -sh . 2>/dev/null || echo "Unable to calculate"

echo ""
echo "💾 Freed space. Ready to run setup-nova-infrastructure.sh"
