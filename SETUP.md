# Setup Instructions for TinyMCE Typer

This document provides detailed instructions for setting up the TinyMCE Typer tool on your system.

- [Prerequisites](#prerequisites)
- [Step 1: Create Project Directory](#step-1-create-project-directory)
- [Step 2: Install System Dependencies](#step-2-install-system-dependencies)
- [Step 3: Set Up Python Virtual Environment](#step-3-set-up-python-virtual-environment)
- [Step 4: Install Python Dependencies](#step-4-install-python-dependencies)
- [Step 5: Create Project Structure](#step-5-create-project-structure)
- [Step 6: Prepare Content Files](#step-6-prepare-content-files)
- [Step 7: Using the Tool](#step-7-using-the-tool)
- [Step 8: Deactivate the Virtual Environment](#step-8-deactivate-the-virtual-environment)
- [Troubleshooting](#troubleshooting)
- [Additional Configuration](#additional-configuration)
- [Updating the Tool](#updating-the-tool)
- [System-Specific Notes](#system-specific-notes)

## Prerequisites

Before you begin, ensure your system meets the following requirements:

- Linux-based operating system (instructions are for Ubuntu/Debian)
- Python 3.x
- Internet connection for downloading dependencies
- Sufficient permissions to install system packages

## Step 1: Create Project Directory

First, create a directory for the project:

```bash
mkdir -p ~/Desktop/tinymce_typer
cd ~/Desktop/tinymce_typer
```

## Step 2: Install System Dependencies

Update your package list and install the required system dependencies:

```bash
sudo apt update
sudo apt install python3-full python3-venv xclip xvfb
```

These packages provide:

- `python3-full`: A complete Python 3 installation
- `python3-venv`: Python virtual environment support
- `xclip`: Command-line interface to the X clipboard
- `xvfb`: Virtual framebuffer X server for headless execution

## Step 3: Set Up Python Virtual Environment

Create and activate a virtual environment to isolate the project dependencies:

```bash
python3 -m venv tinymce_venv
source tinymce_venv/bin/activate
```

Your terminal prompt should change to indicate the activated virtual environment.

## Step 4: Install Python Dependencies

Install the required Python packages:

```bash
pip install selenium webdriver-manager pyperclip
```

These packages provide:

- `selenium`: WebDriver for browser automation
- `webdriver-manager`: Automatic management of browser drivers
- `pyperclip`: Cross-platform clipboard operations

## Step 5: Create Project Structure

Create the scripts directory and the main script file:

```bash
mkdir -p scripts
touch scripts/tinymce_typer.py
```

## Step 6: Prepare Content Files

Create a sample content file that you'll use to populate the TinyMCE editor:

```bash
echo "# Sample Content\n\nThis is some sample content for the TinyMCE editor." > content.md
```

## Step 7: Using the Tool

To use the tool, make sure your virtual environment is activated and run:

```bash
python scripts/tinymce_typer.py <url-to-answer-sheet> ~/Desktop/tinymce_typer/content.md
```

Replace `<url-to-answer-sheet>` with the actual URL of the page containing the TinyMCE editor.

## Step 8: Deactivate the Virtual Environment

When you're done using the tool, deactivate the virtual environment:

```bash
deactivate
```

## Troubleshooting

### Browser Driver Issues

If you encounter issues with browser drivers:

```bash
# For ChromeDriver
pip install webdriver-manager --upgrade
```

### Clipboard Issues

If clipboard operations fail:

```bash
# Verify xclip installation
which xclip

# If not found, install it
sudo apt install xclip
```

### Virtual Environment Problems

If you have issues with the virtual environment:

```bash
# Recreate the environment
rm -rf tinymce_venv
python3 -m venv tinymce_venv
source tinymce_venv/bin/activate
pip install selenium webdriver-manager pyperclip
```

## Additional Configuration

### Creating a Requirements File

To create a requirements file for easier dependency installation:

```bash
pip freeze > requirements.txt
```

This allows others to install dependencies with:

```bash
pip install -r requirements.txt
```

### Setting Up a Development Environment

For development purposes, you might want to install additional packages:

```bash
pip install black flake8 pytest
```

## Updating the Tool

To update the tool to the latest version:

```bash
# Navigate to the project directory
cd ~/Desktop/tinymce_typer

# Pull the latest changes if using git
git pull

# Update dependencies
source tinymce_venv/bin/activate
pip install --upgrade selenium webdriver-manager pyperclip
```

## System-Specific Notes

### Windows Users

For Windows users, the equivalent setup would require:

- Installing Python from the official website
- Using `python -m venv tinymce_venv` to create the virtual environment
- Using `tinymce_venv\Scripts\activate` to activate it
- Installing the Windows version of the required dependencies

### macOS Users

For macOS users:

- Install Python using Homebrew: `brew install python`
- Use `pip3` instead of `pip` if needed
- Install XQuartz for X11 functionality: `brew install --cask xquartz`

[Back to top](#setup-instructions-for-tinymce-typer)
