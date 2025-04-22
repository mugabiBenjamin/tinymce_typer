# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/github/license/mugabiBenjamin/tinymce_typer?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

TinyMCE Typer is a Python automation tool designed to assist with typing content into **TinyMCE** rich text editors and additional compatibility with CKEditor, Quill, and generic contenteditable elements. This utility uses Selenium WebDriver to locate editors on web pages and insert content from text files either character-by-character, in batches, or via clipboard operations. It's particularly useful for situations where you need to transfer large amounts of text into web forms that use rich text editors.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Supported Editors](#supported-editors)
- [Supported File Types](#supported-file-types)
- [Project Structure](#project-structure)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Features

- **Multiple Browser Support:** Works with both Chrome and Firefox browsers
- **Existing Browser Connection:** Connect to already open browser instances
- **Editor Detection:** Automatically detects TinyMCE and other rich text editors
- **Multiple Editor Support:** Can identify and let you select from multiple editors on a page
- **Insertion Methods:**
  - Character-by-character typing with configurable delay
  - Batch insertion for improved performance
  - Clipboard-based pasting
  - HTML-formatted content preservation
- **Progress Tracking:**
  - Real-time progress display
  - Speed calculation (characters per second)
  - Estimated time remaining
- **Session Management:**
  - Save and resume typing progress
  - Optional session encryption for sensitive content
- **Content Verification:** Confirms content was inserted correctly
- **Multiple File Support:** Insert content from multiple files sequentially
- **Browser Profile Support:** Use custom browser profiles

## Prerequisites

Before using TinyMCE Typer, ensure you have the following installed:

- **Python 3.6+**: [Download Python](https://www.python.org/downloads/)
- **Chrome** or **Firefox** browser:
  - [Download Chrome](https://www.google.com/chrome/)
  - [Download Firefox](https://www.mozilla.org/firefox/)
- **WebDriver** for your selected browser (automatically handled by webdriver-manager)
- **Required Python packages**: See the Installation section

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/mugabiBenjamin/tinymce_typer.git
   cd tinymce_typer
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv tinymce_venv

   # On Windows
   tinymce_venv\Scripts\activate

   # On macOS/Linux
   source tinymce_venv/bin/activate
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

The `requirements.txt` file should contain:

```plaintext
selenium
webdriver-manager
pyperclip
cryptography  # Optional, for session encryption
```

## Environment Setup

### Setting up PYTHONPATH

For proper module resolution, create a `.env` file in your project root:

```bash
# Replace with your project path
echo "PYTHONPATH=/home/username/path/to/selenium" > .env
```

### IDE Configuration (VS Code)

Create a `pyrightconfig.json` file for better code intelligence:

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

## Configuration

TinyMCE Typer offers multiple configuration options through command-line arguments:

### Basic Arguments

- `url`: URL of the page with the TinyMCE editor
- `file`: Path to the text file containing content to type

### Browser Options

- `--browser {chrome,firefox}`: Browser to use (default: chrome)
- `--profile PATH`: Path to browser profile directory

### Editor Location Options

- `--iframe-id ID`: ID of the iframe containing TinyMCE
- `--editor-id ID`: ID of the TinyMCE editor element
- `--detect-multiple`: Detect and select from multiple editors

### Content Insertion Options

- `--type-delay SECONDS`: Delay between keystrokes (default: 0.01)
- `--formatted`: Preserve HTML formatting in the content
- `--no-clipboard`: Disable clipboard paste attempt
- `--batch`: Use batch insertion for better performance
- `--batch-size SIZE`: Characters to insert at once (default: 50)
- `--batch-delay SECONDS`: Delay between batch insertions (default: 0.1)

### Session Handling Options

- `--no-session`: Disable session saving/loading
- `--reset`: Reset progress from previous session
- `--encrypt`: Encrypt session data with a password

### Content Verification Options

- `--no-verification`: Disable content verification after typing

### Existing Browser Support

- `--use-existing`: Connect to an existing browser session
- `--debugging-port PORT`: Port for remote debugging (default: 9222)
- `--marionette-port PORT`: Port for Firefox Marionette
- `--force-navigation`: Force navigation to URL with existing browser

### Multi-file Support

- `--files FILE1 FILE2...`: Multiple content files to type sequentially
- `--file-separator SEPARATOR`: Separator between content from multiple files

## Usage

### Basic Usage

- **For faster typing with larger content:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/page-with-editor" "content.md"
  ```

- **For faster typing with larger content:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" "large_content.txt" --batch --batch-size 100
  ```

- **Preserve HTML formatting in your content:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" "formatted_content.html" --formatted
  ```

- **Connect to a running Chrome instance (useful for authenticated sessions):**

  ```bash
  # First, start Chrome with remote debugging enabled
  # chrome.exe --remote-debugging-port=9222

  # Then run the script
  python scripts/tinymce_typer.py "https://example.com/editor" "content.txt" --use-existing --debugging-port 9222
  ```

- **Use a custom browser profile for authentication or specific settings:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" "content.txt" --browser firefox --profile /path/to/firefox/profile
  ```

- **When a page contains multiple editors:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" "content.txt" --detect-multiple
  ```

- **Encrypt your session data for sensitive content:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" "sensitive_content.txt" --encrypt
  ```

- **Insert content from multiple files with custom separators:**

  ```bash
  python scripts/tinymce_typer.py "https://example.com/editor" --files "intro.txt" "body.txt" "conclusion.txt" --file-separator "---\n\n"
  ```

### Advanced Usage Examples

1. **Using Firefox with batch insertion:**

   ```bash
   python scripts/tinymce_typer.py "https://example.com/page" "content.md" --browser firefox --batch
   ```

2. **Preserving HTML formatting:**

   ```bash
   python scripts/tinymce_typer.py "https://example.com/page" "content.html" --formatted
   ```

3. **Using an existing Chrome session:**

   ```bash
   # First, start Chrome with remote debugging enabled:
   # chrome.exe --remote-debugging-port=9222

   python scripts/tinymce_typer.py "https://example.com/page" "content.md" --use-existing --debugging-port 9222
   ```

4. **Typing multiple files:**

   ```bash
   python scripts/tinymce_typer.py "https://example.com/page" "placeholder.txt" --files intro.md main.md conclusion.md
   ```

5. **With encrypted session data:**

   ```bash
   python scripts/tinymce_typer.py "https://example.com/page" "content.md" --encrypt
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

## Supported Editors

TinyMCE Typer can work with various rich text editors:

- **TinyMCE**: Primary supported editor (various versions)
- **CKEditor**: Basic support for common implementations
- **Quill Editor**: Basic support
- **Generic contenteditable elements**: Any element with the contenteditable attribute

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

## Security

When working with sensitive content, consider these security features:

- **Session Encryption**: Use the `--encrypt` flag to protect saved session data
- **Browser Profiles**: Use a dedicated profile with `--profile` to isolate the automation

To enable encryption, ensure the cryptography package is installed:

```bash
pip install cryptography
```

## Troubleshooting

### Editor Not Found

If the script cannot find the editor:

1. Ensure the page is fully loaded before pressing Enter to start typing
2. Try providing the iframe ID with `--iframe-id`
3. Try providing the editor ID with `--editor-id`
4. Check if the editor is in an iframe structure

### Connection Issues

If using `--use-existing` with Chrome:

1. Close all Chrome instances
2. Start Chrome with: `chrome.exe --remote-debugging-port=9222`
3. Run the script with `--use-existing --debugging-port 9222`

### Content Not Inserted Correctly

If content verification fails:

1. Try decreasing the typing speed with a higher `--type-delay`
2. Use `--batch` mode with `--batch-size` to adjust chunk size
3. Use `--formatted` if your content contains HTML

## Notes

- **Performance Considerations**: For very large files (>1MB), consider using batch mode (`--batch`) with a larger batch size for better performance.
- **Browser Memory**: Chrome typically handles larger content better than Firefox, though this may vary depending on your system.
- **Website Limitations**: Some websites may have anti-automation measures that could affect typing or pasting operations.
- **Session Files**: The session file (`tinymce_session.json`) is created in the same directory where the script is run. These files are small but may contain sensitive information if encryption is not used.
- **System Resources**: When running with large files, ensure your system has sufficient memory available, especially if using batch mode with large batch sizes.
- **Testing**: It's recommended to test with small content samples before attempting to insert large documents, particularly when using a new website or editor configuration.

## Contributing

Contributions to TinyMCE Typer are welcome! To contribute:

1. Fork the repository

2. Create a feature branch

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. Commit your changes

   ```bash
   git commit -m 'Add amazing feature
   ```

4. Push to the branch

   ```bash
   git push origin feature/amazing-feature
   ```

5. Open a Pull Request

_Please ensure your code follows the project's style guidelines and includes appropriate tests._

## License

This project is licensed under the terms of the license included in the repository. See the [LICENSE](LICENSE) file for details.

## Feedback

- Found a bug or have a feature request? Please open an [Issue](https://github.com/mugabiBenjamin/tinymce_typer/issues) on GitHub.
- Want to contribute? Pull requests are welcome! See the [Contributing section](#contributing) for more details.

## Acknowledgements

- Selenium WebDriver
- TinyMCE
- Pyperclip

Made with ❤️ by the **Hybrids**

**Note**: _This tool is provided for legitimate content insertion purposes. Always respect website terms of service and avoid overloading servers with automated requests._

[Back to top](#tinymce-typer)
