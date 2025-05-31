#!/bin/bash

# Enhanced Voice Assistant Installation Script
# This script sets up the voice assistant on your system

set -e  # Exit on any error

echo "🎤 Enhanced Voice Assistant Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Install system dependencies (Ubuntu/Debian)
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            python3-pip \
            python3-venv \
            portaudio19-dev \
            python3-pyaudio \
            espeak \
            ffmpeg \
            git \
            curl
        print_success "System dependencies installed"
    elif command -v yum &> /dev/null; then
        sudo yum install -y \
            python3-pip \
            portaudio-devel \
            espeak \
            ffmpeg \
            git \
            curl
        print_success "System dependencies installed"
    else
        print_warning "Could not detect package manager. Please install manually:"
        echo "- portaudio19-dev (for PyAudio)"
        echo "- espeak (for TTS)"
        echo "- ffmpeg (for audio processing)"
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    print_success "Virtual environment activated"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Created .env file from template"
        print_warning "Please edit .env file with your API keys before running!"
    else
        print_warning ".env file already exists"
    fi
}

# Create activation sound if it doesn't exist
setup_assets() {
    print_status "Setting up assets..."
    
    mkdir -p assets
    
    if [ ! -f "assets/plop.mp3" ]; then
        print_warning "plop.mp3 not found. Creating placeholder..."
        # Create a simple beep sound using ffmpeg if available
        if command -v ffmpeg &> /dev/null; then
            ffmpeg -f lavfi -i "sine=frequency=800:duration=0.3" -ac 2 assets/plop.mp3 2>/dev/null || true
        fi
    fi
    
    print_success "Assets setup complete"
}

# Set permissions
set_permissions() {
    print_status "Setting up permissions..."
    chmod +x main.py
    print_success "Permissions set"
}

# Main installation function
main() {
    echo
    print_status "Starting installation process..."
    
    check_python
    install_system_deps
    setup_venv
    install_python_deps
    setup_env
    setup_assets
    set_permissions
    
    echo
    print_success "Installation completed successfully! 🎉"
    echo
    echo "Next steps:"
    echo "1. Edit the .env file with your API keys:"
    echo "   nano .env"
    echo
    echo "2. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo
    echo "3. Run the assistant:"
    echo "   python main.py"
    echo
    print_warning "Don't forget to configure your API keys in .env!"
}

# Run main function
main
