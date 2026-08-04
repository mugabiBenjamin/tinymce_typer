# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

TinyMCE Typer is a Python automation tool for inserting content from local text-based files into browser-based rich text editors. It is primarily designed for **TinyMCE**, with best-effort compatibility for **CKEditor**, **Quill**, and generic `contenteditable` elements.

The tool uses Selenium WebDriver to open or attach to a browser, locate a supported editor, insert content using the selected insertion method, track progress, optionally save resumable session data, and verify whether the final editor content appears to match the source.

> **Important:** This project automates browser interaction. Use it only for legitimate content insertion, respect website terms of service, and avoid overloading or bypassing systems that prohibit automation.

## Table of Contents

- [TinyMCE Typer](#tinymce-typer)
  - [Table of Contents](#table-of-contents)
  - [Support Status](#support-status)
  - [Features](#features)
  - [Safety and Limitations](#safety-and-limitations)
    - [Direct DOM insertion limitations](#direct-dom-insertion-limitations)
    - [Clipboard behavior](#clipboard-behavior)
    - [Browser profiles and authenticated sessions](#browser-profiles-and-authenticated-sessions)
    - [Known limitations](#known-limitations)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Windows](#windows)
    - [macOS](#macos)
    - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
  - [Supported File Types](#supported-file-types)
  - [Usage](#usage)
    - [Basic usage](#basic-usage)
    - [Use Firefox](#use-firefox)
    - [Specify a TinyMCE iframe ID](#specify-a-tinymce-iframe-id)
    - [Use an authenticated browser profile](#use-an-authenticated-browser-profile)
    - [Connect to an existing Chrome session](#connect-to-an-existing-chrome-session)
    - [Batch mode for large files](#batch-mode-for-large-files)
    - [Reset saved progress](#reset-saved-progress)
  - [Command-Line Options](#command-line-options)
    - [Required arguments](#required-arguments)
    - [Browser options](#browser-options)
    - [Editor location options](#editor-location-options)
    - [Content insertion options](#content-insertion-options)
    - [Session options](#session-options)
  - [Changelog](#changelog)
    - [\[Unreleased\]](#unreleased)
      - [Documentation](#documentation)
      - [Repository hygiene](#repository-hygiene)
      - [Planned refactor milestones](#planned-refactor-milestones)
    - [\[0.1.0\] — Initial project state](#010--initial-project-state)
      - [Added](#added)

## Support Status

| Area | Status | Notes |
| --- | --- | --- |
| TinyMCE | Primary support | The tool searches for common TinyMCE iframe patterns and can target known iframe/editor IDs. |
| CKEditor | Best-effort support | Detection is available for common CKEditor iframe structures, but behavior can vary by CKEditor version and site configuration. |
| Quill | Best-effort support | Detection targets `.ql-editor`, but full Quill state synchronization may require editor-native APIs in future versions. |
| Generic `contenteditable` | Fallback support | Useful when no known editor framework is detected, but reliability depends heavily on the website. |
| Clipboard insertion | Best-effort support | Depends on the operating system clipboard backend, browser permissions, and website behavior. |
| Direct HTML insertion | Fast but limited | Updates DOM content directly and may not trigger all editor/framework events. |
| Batch insertion | Performance-oriented | Useful for large content, but still needs verification. |
| Character insertion | Compatibility-oriented | Slower and may not behave like true human typing in every editor. |
| Session resume | Basic support | Resume is based on saved progress; future versions should include stronger file hashing and editor identity checks. |
| Verification | Basic support | Uses normalized content comparison; formatting or editor-generated markup can affect results. |

## Features

- Rich text editor detection for TinyMCE, CKEditor, Quill, and generic `contenteditable` elements.
- Multiple insertion modes: clipboard, formatted/direct HTML, batch insertion, and character-based insertion.
- Whitespace and line-break preservation for plain text content.
- Support for Chrome and Firefox.
- Browser profile support for sites that require authentication.
- Ability to connect to an existing browser session.
- Multiple input files with configurable separators.
- Progress display with estimated speed and remaining time.
- Optional resumable sessions.
- Optional encrypted session data when encryption dependencies are available.
- Basic post-insertion verification.

## Safety and Limitations

### Direct DOM insertion limitations

Some insertion paths use direct DOM updates such as setting editor HTML content. This can be fast, but it is not always equivalent to real user typing.

Direct DOM insertion may fail to trigger:

- editor change events
- framework state updates
- autosave hooks
- dirty-state tracking
- validation logic
- undo history
- custom website event handlers

Always review the inserted content before submitting a form. If a website depends heavily on JavaScript framework state, direct DOM insertion may appear successful visually while the underlying form state remains unchanged.

### Clipboard behavior

Clipboard insertion depends on the operating system, browser, permissions, and installed clipboard utilities. On Linux, clipboard operations may require `xclip` or `wl-clipboard` depending on the display server.

The tool may temporarily overwrite your clipboard while inserting content. Future versions should make clipboard restoration stricter across all success and failure paths.

### Browser profiles and authenticated sessions

Browser profiles can help when a website requires login, but they also carry risk. A browser profile may contain active sessions, cookies, saved logins, extensions, and personal browsing state.

Use browser profiles carefully:

- Prefer a dedicated automation browser profile.
- Avoid using a profile that contains sensitive sessions unless necessary.
- Review the page manually before submitting content.
- Do not run automation against pages where accidental submission would cause harm.
- Avoid pages containing password fields or destructive actions.

### Known limitations

- Editor support varies by website and editor version.
- Some websites block automation, pasting, or scripted DOM changes.
- Verification is basic and may not catch all formatting differences.
- Resume behavior can be unsafe if the source file changes after progress is saved.
- Direct HTML insertion can create malformed or unexpected markup if the source content is not prepared correctly.
- Firefox existing-session support is experimental.
- Very large files may require batch mode and enough browser memory.
- The browser intentionally remains open after completion for manual review unless lifecycle behavior is changed in future versions.

## Prerequisites

Before using TinyMCE Typer, install:

1. **Python 3.12+**
2. **uv** for dependency management
3. **Chrome** or **Firefox**
4. A clipboard utility when using clipboard mode on Linux:
   - X11: `xclip`
   - Wayland: `wl-clipboard`

## Installation

### Windows

```powershell
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce_typer
uv sync
```

### macOS

```bash
git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce_typer
uv sync
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y xclip

git clone https://github.com/mugabiBenjamin/tinymce_typer.git
cd tinymce_typer
uv sync
```

For Wayland:

```bash
sudo apt install -y wl-clipboard
```

## Supported File Types

TinyMCE Typer is intended for text-based files:

- `.txt`
- `.md` / `.markdown`
- `.html` / `.htm`
- `.rtf` — basic text extraction only
- `.xml`
- `.js`, `.css`, `.py`, and other code files
- `.csv` / `.tsv`
- `.json`

When inserting HTML content and preserving formatting, use formatted mode and ensure the HTML is compatible with the target editor.

## Usage

### Basic usage

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt
```

### Use Firefox

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser firefox
```

### Specify a TinyMCE iframe ID

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --iframe-id tinymce_ifr
```

### Use an authenticated browser profile

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --profile "/path/to/browser/profile"
```

Prefer a dedicated automation profile instead of your daily personal browser profile.

### Connect to an existing Chrome session

Start Chrome with remote debugging enabled:

```bash
google-chrome --remote-debugging-port=9222
```

Then connect the script:

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --use-existing --debugging-port=9222
```

### Batch mode for large files

```bash
uv run scripts/tinymce_typer.py https://example.com/editor large_content.txt --batch --batch-size 100 --batch-delay 0.05
```

### Reset saved progress

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --reset
```

## Command-Line Options

### Required arguments

| Argument | Description |
| --- | --- |
| `url` | URL of the page containing the editor |
| `file` | Path to the text file with content to insert |

### Browser options

| Option | Description |
| --- | --- |
| `--browser {chrome,firefox}` | Browser to use. Default: `chrome` |
| `--profile PROFILE` | Path to browser profile directory |
| `--use-existing` | Attach to an existing browser session |
| `--debugging-port PORT` | Remote debugging port for an existing Chrome session. Default: `9222` |

### Editor location options

| Option | Description |
| --- | --- |
| `--iframe-id IFRAME_ID` | ID of the iframe containing TinyMCE |
| `--editor-id EDITOR_ID` | ID of the editor element |
| `--detect-multiple` | Detect and select from multiple editors on the page |

### Content insertion options

| Option | Description |
| --- | --- |
| `--type-delay TYPE_DELAY` | Delay between characters in seconds. Default: `0.01` |
| `--formatted` | Preserve HTML formatting in the content |
| `--no-clipboard` | Disable clipboard paste attempt |
| `--batch` | Use batch insertion mode |
| `--batch-size BATCH_SIZE` | Characters per batch. Default: `50` |
| `--batch-delay BATCH_DELAY` | Delay between batches in seconds. Default: `0.1` |

### Session options

| Option | Description |
| --- | --- |
| `--no-session` | Disable session saving and loading |
| `--reset` | Reset any saved progress for the given URL and file |

## Changelog

All notable changes to this project will be documented here. The format is based on Keep a Changelog conventions, and this project uses semantic versioning once formal releases begin.

### [Unreleased]

#### Documentation

- Clarified that TinyMCE is the primary supported editor target.
- Clarified that CKEditor, Quill, and generic `contenteditable` support are currently best-effort.
- Added warnings about direct `innerHTML`/DOM insertion not always triggering editor or framework events.
- Added safer usage notes for browser profiles and authenticated sessions.
- Clarified clipboard behavior and operating-system dependency risks.
- Added known limitations for verification, resume behavior, browser automation, and large files.
- Linked this changelog from the README.

#### Repository hygiene

- Added `.env.example` for future configuration defaults.
- Cleaned and categorized `.gitignore` entries.
- Added missing MIT `LICENSE` file for consistency with the README license statement.

#### Planned refactor milestones

These are not yet implemented but define the next architectural direction:

- Split CLI parsing from browser automation logic.
- Introduce a typed settings/config object.
- Extract content loading and formatting into a content module.
- Extract browser setup into Chrome and Firefox providers.
- Extract editor detection into editor-specific adapters.
- Extract insertion behavior into strategy classes.
- Extract session persistence and encryption into session modules.
- Extract verification into a dedicated verifier module.
- Add logging, custom exceptions, diagnostics, tests, and packaging improvements.
- Apply separation of concerns and SOLID principles throughout the refactor.

### [0.1.0] — Initial project state

#### Added

- Selenium-based browser automation for inserting content into rich text editors.
- TinyMCE-oriented editor detection.
- Best-effort CKEditor, Quill, and generic `contenteditable` detection.
- Clipboard, formatted/direct insertion, batch insertion, and character-based insertion modes.
- Single-file and multi-file content loading.
- Basic progress tracking.
- Basic resumable session support.
- Optional encrypted session storage when encryption dependencies are available.
- Basic content verification.

[Back to Top](#tinymce-typer)
