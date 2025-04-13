# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/github/license/mugabiBenjamin/tinymce_typer?style=flat-square)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

A Python script to automate typing or pasting content into [TinyMCE](https://www.tiny.cloud/) editors using Selenium — great for filling in online text editors like vClass coursework pages using content from local markdown files.

- [Features](#features)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Contributing](#contributing)
- [Notes](#notes)
- [License](#license)
- [Feedback](#feedback)

## Features

- Automates typing/pasting into TinyMCE editors via Selenium
- Clipboard support using `pyperclip`
- Headless-compatible with `xvfb`
- Local Markdown file input
- Works with Chromium and Chrome browsers

## Project Structure

```plaintext
├── scripts/
│   ├── tinymce_typer.py    # Main script file
├── .gitignore              # Specifies files and directories to be ignored by Git
├── content.md              # Main content or documentation file
├── README.md               # Project overview and instructions
├── requirements.txt        # List of Python dependencies for the project
└── SETUP.txt                # Setup instructions or configuration details
```

## Setup Instructions

- You can follow [SETUP](SETUP.md).

## Usage

- Run the script using the following command:

```bash
python scripts/tinymce_typer.py <URL> <markdown_file>
```

- Example

```bash
python scripts/tinymce_typer.py https://vclass.ac/dashboard/course-work/ongoing/RGLDmZLV9Am content.md
```

## Contributing

### 1. Fork the repository

### 2. Clone the repository

```bash
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce_typer/
```

### 3. Create a new branch

```bash
git checkout -b feature/branch-name
```

### 4. Make your changes and commit them

```bash
git add .
git commit -m "Add new feature"
```

### 5. Push your changes to your forked repository

```bash
git push origin feature/branch-name
```

### 6. Submit a pull request to the original repository

## Notes

- Always activate your environment before running the script:

```bash
source tinymce_venv/bin/activate
```

- To freeze the current environment (if you install new packages):

```bash
pip freeze > requirements.txt
```

## License

- This project is licensed under the [MIT License](LICENSE).

## Feedback

- Feel free to open an [issue](https://github.com/mugabiBenjamin/tinymce_typer/issues) or contribute if you'd like to improve this script.
