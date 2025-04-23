# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/github/license/mugabiBenjamin/tinymce_typer?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

TinyMCE Typer is a Python automation tool designed to assist with typing content into **TinyMCE** rich text editors and additional compatibility with CKEditor, Quill, and generic contenteditable elements. This utility uses Selenium WebDriver to locate editors on web pages and insert content from text files either character-by-character, in batches, or via clipboard operations. It's particularly useful for situations where you need to transfer large amounts of text into web forms that use rich text editors.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Supported File Types](#supported-file-types)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)
- [Contributing](#contributing)
- [License](#license)
- [Feedback](#feedback)
- [Acknowledgements](#acknowledgements)

## Features

- **Rich Text Editor Support**: Works with TinyMCE, CKEditor, Quill, and generic contenteditable elements
- **Multiple Input Methods**: Character-by-character typing, batch insertion, and clipboard pasting
- **Whitespace Preservation**: Maintains all whitespace, indentation, and line breaks from source files
- **Progress Tracking**: Shows typing progress with speed and estimated time remaining
- **Session Management**: Save and resume typing sessions with optional encryption
- **Multi-Browser Support**: Works with Chrome and Firefox
- **Multiple File Input**: Combine content from multiple files
- **Browser Profile Support**: Use existing browser profiles for authentication
- **Existing Browser Connection**: Connect to already running browser instances

## Installation

### Prerequisites

Before using TinyMCE Typer, ensure you have the following installed:

1. **Python 3.6+**: [Download Python](https://www.python.org/downloads/)

2. **Chrome** or **Firefox** browser:

   - [Download Chrome](https://www.google.com/chrome/)
   - [Download Firefox](https://www.mozilla.org/firefox/)

3. **Required Python packages**

   ```bash
   # All platforms
   pip install selenium webdriver-manager pyperclip

   # Optional: For session encryption
   pip install cryptography
   ```

### Platform-Specific Setup

#### Windows

```powershell
# Clone repository (if using git)
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce-typer

# Install requirements
pip install -r requirements.txt
```

#### macOS

```bash
# Clone repository (if using git)
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce-typer

# Install requirements
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt update
sudo apt install -y python3-pip xclip

# Clone repository (if using git)
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce-typer

# Install requirements
pip3 install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Windows
python tinymce_typer.py https://example.com/page-with-editor your_content_file.txt

# macOS/Linux
python3 tinymce_typer.py https://example.com/page-with-editor your_content_file.txt
```

### Examples

1. **Basic usage with Chrome (default)**:

   ```bash
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt
   ```

2. **Use Firefox instead of Chrome**:

   ```bash
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --browser firefox
   ```

3. **Specify TinyMCE iframe ID (if known)**:

   ```bash
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --iframe-id tinymce_ifr
   ```

4. **Use browser profile for authenticated sessions**:

   ```bash
   # Windows Chrome
   python tinymce_typer.py https://example.com/page-with-editor content.txt --profile "C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Default"

   # macOS Chrome
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --profile "/Users/YourUsername/Library/Application Support/Google/Chrome/Default"

   # Linux Chrome
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --profile "/home/yourusername/.config/google-chrome/Default"

   # Firefox (all platforms)
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --browser firefox --profile "/path/to/firefox/profile"
   ```

5. **Connect to existing browser (advanced)**:

   ```bash
   # Start Chrome with remote debugging (Windows)
   start chrome --remote-debugging-port=9222

   # Start Chrome with remote debugging (macOS/Linux)
   google-chrome --remote-debugging-port=9222

   # Then connect the script
   python3 tinymce_typer.py https://example.com/page-with-editor content.txt --use-existing --debugging-port=9222
   ```

### Command Line Options

#### Basic Options

```bash
# positional arguments:
  url                   # URL of the page with TinyMCE editor
  file                  # Path to the text file containing content to type

# optional arguments:
  -h, --help            # Show this help message and exit
```

#### Browser Options

```bash
  --browser {chrome,firefox}
                        # Browser to use (default: chrome)
  --profile PROFILE     # Path to browser profile directory
```

#### Editor Location Options

```bash
--iframe-id IFRAME_ID
                        # ID of the iframe containing TinyMCE (if applicable)
--editor-id EDITOR_ID
                        # ID of the TinyMCE editor element (if known)
--detect-multiple       # Detect and select from multiple TinyMCE editors
```

#### Content Insertion Options

```bash
  --type-delay TYPE_DELAY
                        # Delay between keystrokes in seconds (default: 0.01)
  --formatted           # Preserve HTML formatting in the content
  --no-clipboard        # Disable clipboard paste attempt
  --batch               # Use batch insertion for better performance
  --batch-size BATCH_SIZE
                        # Number of characters to insert at once (default: 50)
  --batch-delay BATCH_DELAY
                        # Delay between batch insertions in seconds (default: 0.1)
```

#### Session Handling Options

```bash
  --no-session          # Disable session saving/loading
  --reset               # Reset progress from previous session
  --encrypt             # Encrypt session data with a password
```

#### Content Verification Options

```bash
  --no-verification     # Disable content verification after typing
```

#### Existing Browser Support

```bash
  --use-existing        # Connect to an existing browser session instead of starting new one
  --debugging-port DEBUGGING_PORT
                        # Port for remote debugging (default: 9222, used with --use-existing)
  --marionette-port MARIONETTE_PORT
                        # Port for Firefox Marionette (used with --use-existing for Firefox)
  --force-navigation    # Force navigation to URL even when using existing browser
```

#### Multi-file Support

```bash
  --files [FILES ...]   # Multiple content files to type sequentially
  --file-separator FILE_SEPARATOR
                        # Separator to use between content from multiple files (default: \n\n)
```

## Troubleshooting

### Browser Driver Issues

If you encounter browser driver errors:

1. **Update webdriver-manager**:

   ```bash
   pip install --upgrade webdriver-manager
   ```

2. **Manual driver installation**:

   - Chrome: Download [ChromeDriver](https://sites.google.com/chromium.org/driver/) matching your Chrome version
   - Firefox: Download [GeckoDriver](https://github.com/mozilla/geckodriver/releases)

### Editor Detection Issues

If the script cannot find the editor:

1. Try using the developer tools in your browser to inspect the editor element
2. Find the relevant iframe ID or editor ID and specify it using `--iframe-id` or `--editor-id`
3. Use `--detect-multiple` to let the script detect and offer a choice of editors

### Whitespace Preservation Issues

The latest version includes enhanced whitespace preservation. If you still experience whitespace issues:

1. Use the `--formatted` flag to enable HTML formatting preservation
2. For complex formatting, consider using HTML formatting in your source file

### Linux-Specific Issues

1. **Clipboard functionality**:

   - Ensure `xclip` is installed: `sudo apt install xclip`
   - For Wayland users, install `wl-clipboard`: `sudo apt install wl-clipboard`

2. **Browser path issues**:
   - Chrome: If Chrome isn't found, specify the binary location in the script
   - Firefox: If Firefox isn't found, specify the binary location in the script

## Advanced Features

### Using Encrypted Sessions

To enable encryption for session data (requires the `cryptography` package):

```bash
python3 tinymce_typer.py https://example.com content.txt --encrypt
```

You'll be prompted for a password to encrypt the session data.

### Content Verification

By default, the script verifies the typed content matches the source file. Disable with:

```bash
python3 tinymce_typer.py https://example.com content.txt --no-verification
```

### Performance Optimization

For large content files, use batch mode for better performance:

```bash
python3 tinymce_typer.py https://example.com content.txt --batch --batch-size 100 --batch-delay 0.05
```

## Recent Improvements

### Whitespace Preservation Enhancement

The latest version includes significant improvements to whitespace handling:

- Properly preserves line breaks and indentation from source files
- Maintains consecutive spaces and tabs
- Works across different rich text editor implementations
- Implemented in all typing methods (character-by-character, batched, clipboard)

## Supported File Types

TinyMCE Typer works with various text-based file formats:

- **Plain text files** (`.txt`): Standard text without formatting
- **Markdown files** (`.md`, `.markdown`): Preserves Markdown syntax
- **HTML files** (`.html`, `.htm`): Can preserve HTML formatting when used with `--formatted` flag
- **Rich Text Format** (`.rtf`): Basic support (text content only)
- **XML files** (`.xml`): Text content is preserved
- **JavaScript/CSS/Code files** (`.js`, `.css`, `.py`, etc.): Code can be inserted as-is
- **CSV/TSV files** (`.csv`, `.tsv`): Will preserve structure but may not format as tables
- **JSON files** (`.json`): Content will be inserted as raw text

When inserting HTML content into an editor and preserving formatting:

1. Use the `--formatted` flag
2. Ensure your HTML file uses tags compatible with the editor
3. Consider using multiple files with `--files` if you need to insert different sections with varied formatting

## Configuration

### Environment Setup

- For proper module resolution, create a `.env` file in your project root:

```bash
# Replace with your project path
echo "PYTHONPATH=/home/username/path/to/selenium" > .env
```

### IDE Configuration (VS Code)

- Create a `pyrightconfig.json` file for better code intelligence:

```json
{
  "venvPath": ".",
  "venv": "tinymce_venv",
  "pythonVersion": "3.12",
  "extraPaths": ["./tinymce_venv/lib/python3.12/site-packages"],
  "typeCheckingMode": "off",
  "useLibraryCodeForTypes": true,
  "python.envFile": "${workspaceFolder}/.env"
}
```

### Resumable Content Insertion

- For very large content that might need to be resumed:

  ```bash
  # Initial run
  python scripts/tinymce_typer.py https://example.com/editor large_content.txt --batch

  # If interrupted, resume later
  python scripts/tinymce_typer.py https://example.com/editor large_content.txt --batch
  # (The script will detect the previous session and offer to resume)
  ```

### Content Verification for Critical Applications

- When accuracy is crucial:

  ```bash
  python tinymce_typer.py https://example.com/editor important_content.txt --type-delay 0.05
  # (Default verification will run, or explicitly use --no-verification to disable)
  ```

### Usage Workflow

1. The script will launch or connect to a browser and navigate to the specified URL
2. It will attempt to locate the rich text editor on the page
3. If multiple editors are found, you may be prompted to select one
4. The script will try different methods to insert the content:
   - First, it attempts `clipboard pasting` (if not disabled)
   - If pasting fails, it falls back to `typing methods`
5. Progress is displayed in real-time with speed and ETA
6. After typing completes, content verification checks if the text was inserted correctly
7. The browser remains open for you to review and submit the form

## Project Structure

The project is organized as follows:

```plaintext
tinymce_typer/
├── scripts/
│   └── tinymce_typer.py   # Main script
├── content.md             # Sample content file
├── README.md              # Project documentation
├── SETUP.md               # Additional setup instructions
├── requirements.txt       # Python dependencies
├── LICENSE                # License information
├── pyrightconfig.json     # Python language server configuration
├── .env                   # Environment variables
└── tinymce_venv/          # Virtual environment (not tracked in git)
```

## Notes

- **Performance Considerations**: For very large files (>1MB), consider using batch mode (`--batch`) with a larger batch size for better performance.
- **Browser Memory**: Chrome typically handles larger content better than Firefox, though this may vary depending on your system.
- **Website Limitations**: Some websites may have anti-automation measures that could affect typing or pasting operations.
- **Session Files**: The session file (`tinymce_session.json`) is created in the same directory where the script is run. These files are small but may contain sensitive information if encryption is not used.
- **System Resources**: When running with large files, ensure your system has sufficient memory available, especially if using batch mode with large batch sizes.
- **Testing**: It's recommended to test with small content samples before attempting to insert large documents, particularly when using a new website or editor configuration.

## Contributing

Contributions to TinyMCE Typer are welcome! To contribute:

## License

- This project is licensed under the terms of the license included in the repository. See the [MIT License](./LICENSE) file for details.

## Feedback

- Found a bug or have a feature request? Please open an [Issue](https://github.com/mugabiBenjamin/tinymce_typer/issues) on GitHub.

## Acknowledgements

- Selenium WebDriver
- TinyMCE
- Pyperclip

Made with ❤️ by the **Hybrids**

**Note**: _This tool is provided for legitimate content insertion purposes. Always respect website terms of service and avoid overloading servers with automated requests._

[Back to top](#tinymce-typer)
