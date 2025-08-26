#!/bin/bash

echo "🚀 Setting up Jarvis Study Detection..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup complete! To get started:"
echo ""
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set your ElevenLabs API key:"
echo "   Option 1: Copy env.example to .env and edit it"
echo "   Option 2: export ELEVEN_API_KEY='your_api_key_here'"
echo ""
echo "3. Update config.json with your VOICE_ID"
echo ""
echo "4. Test the setup:"
echo "   python test_imports.py"
echo ""
echo "5. Run the app:"
echo "   python main.py"
echo ""
echo "Happy studying! 📚✨"
