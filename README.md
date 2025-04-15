# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/github/license/mugabiBenjamin/tinymce_typer?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

A Python automation tool for populating [TinyMCE](https://www.tiny.cloud/) editors in web applications with content from various text-based files.

- [Overview](#overview)
- [Features](#features)
- [Supported Files Types](#supported-file-types)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
  - [Project Structure](#project-structure)
  - [Contributing](#contributing)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
- [Feedback](#feedback)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Overview

**TinyMCE Typer** is a utility for automating text input into TinyMCE-based rich text editors on web pages. It uses Selenium WebDriver to interact with browsers and input content from text files into TinyMCE editors, which can be useful for testing, content migration, or form automation.

## Features

- Automatically populate TinyMCE editors with content from text-based files
- Supports multiple file formats including `markdown`, `plain text`, and more
- Supports headless operation through `Xvfb`
- Clipboard-based content insertion for more reliable text input
- Compatible with most TinyMCE-enabled websites

## Supported File Types

**The tool works with various text-based file types:**

- Markdown files (`.md`, `.markdown`)
- Plain text files (`.txt`)
- HTML files (`.html`, `.htm`) - content can be extracted and inserted
- Any text-based file can be used (`.csv`, `.json`, `.xml`, etc.)

**For Selenium WebDriver functionality:**

- Python script files (`.py`)
- WebDriver configuration files (`.json`)
- Browser-specific driver executables (no extension for Linux, `.exe` for Windows)
- Log files (`.log`)

## Prerequisites

- Python 3.x
- Linux environment (commands are Ubuntu/Debian-based)
- Access to websites with TinyMCE editors

## Installation

### Option 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/mugabiBenjamin/tinymce_typer.git

# Navigate to the project directory
cd tinymce_typer

# Create and activate a virtual environment
python3 -m venv tinymce_venv
source tinymce_venv/bin/activate

# Install required packages
pip install selenium webdriver-manager pyperclip

# Install system dependencies
sudo apt install xclip xvfb
```

### Option 2: Manual Setup

For detailed setup instructions, please refer to the [SETUP.md](SETUP.md) file.

## Usage

1. Activate the virtual environment

```bash
source tinymce_venv/bin/activate
```

2. Run the script with a URL to the page containing the TinyMCE editor and the path to your content file

```bash
python scripts/tinymce_typer.py <URL> <content_file>
```

### Example

- You can use any text-based file as input:

```bash
# Using markdown
python ~/Desktop/tinymce_typer/scripts/tinymce_typer.py <url> ~/Desktop/tinymce_typer/content.md

# Using plain text
python ~/Desktop/tinymce_typer/scripts/tinymce_typer.py <url> ~/Desktop/tinymce_typer/content.txt

# Using HTML
python ~/Desktop/tinymce_typer/scripts/tinymce_typer.py <url> ~/Desktop/tinymce_typer/content.html
```

3. When finished, deactivate the virtual environment

```bash
deactivate
```

## Configuration

The tool uses default configurations that work with most TinyMCE implementations. Advanced configuration options can be found in the [Script](scripts/tinymce_typer.py) file.

## Development

### Project Structure

```plaintext
tinymce_typer/
├── scripts/
│   └── tinymce_typer.py        # Main script file
├── tinymce_venv/
├── content.md                  # Main content file
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview and instructions
├── SETUP.md                    # Detailed setup instructions
├── LICENSE                     # License file
└── .gitignore                  # Git ignore rules
```

### Contributing

1. Fork the repository

2. Create your feature branch

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes

```bash
git commit -m 'Add some amazing feature'
```

4. Push to the branch

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request

## Notes

- Always activate your environment before running the script:

```bash
source tinymce_venv/bin/activate
```

- To freeze the current environment (if you install new packages):

```bash
pip freeze > requirements.txt
```

- The script uses `Selenium WebDriver`, which requires the appropriate browser driver to be installed. The script will attempt to download the necessary driver automatically.
- The script may not work with all TinyMCE implementations due to variations in editor configurations and DOM structure.
- For large content files, the script may take some time to process. Be patient and do not interrupt the process.

## Troubleshooting

- **Script can't find the TinyMCE editor:** Make sure the page has fully loaded and the TinyMCE editor is present.
- **Content not pasting correctly:** Check that xclip is properly installed and functioning.
- **Browser doesn't start:** Check that you have the correct drivers installed for Selenium.

## Feedback

- Found a bug or have a feature request? Please open an [Issue](https://github.com/mugabiBenjamin/tinymce_typer/issues) on GitHub.
- Want to contribute? Pull requests are welcome! See the [Contributing section](#contributing) for more details.

## License

Distributed under the [MIT License](LICENSE). See LICENSE for more information.

## Acknowledgements

- Selenium WebDriver
- TinyMCE
- Pyperclip

Made with ❤️ by the **Hybrids**

[Back to top](#tinymce-typer)
