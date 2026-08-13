# TinyMCE Typer

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)
![Status](https://img.shields.io/badge/status-active-success?style=flat-square)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square&logo=github)

TinyMCE Typer is a Python/Selenium automation tool for inserting content from local UTF-8 text-based files into browser-based rich text editors.

TinyMCE is the primary target. CKEditor, Quill, and generic `contenteditable` elements are supported on a best-effort basis through editor adapters.

The project has been refactored into a modular architecture:

- browser providers and lifecycle handling
- local and remote browser support
- platform/environment diagnostics
- content loading, formatting, sanitization, and hashing
- editor detection and editor-specific adapters
- insertion strategies with fallback chaining
- resumable and optionally encrypted sessions
- verification modes and failure artifacts
- progress reporters
- terminal and JSON output writers
- application orchestration through `TyperApp`
- contracts/protocols for SOLID boundaries

> **Important:** This project automates browser interaction. Use it only for legitimate content insertion, respect website terms of service, and avoid automating pages where accidental submission, duplicate posting, or data loss could cause harm.

## Table of Contents

- [Support Status](#support-status)
- [Features](#features)
- [Safety and Limitations](#safety-and-limitations)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Supported File Types](#supported-file-types)
- [Usage](#usage)
- [Browser Providers](#browser-providers)
- [RemoteWebDriver / Selenium Grid](#remotewebdriver--selenium-grid)
- [Insertion Strategies](#insertion-strategies)
- [Sessions and Resume Safety](#sessions-and-resume-safety)
- [Verification](#verification)
- [Progress Reporting](#progress-reporting)
- [JSON Output](#json-output)
- [Diagnostics](#diagnostics)
- [Configuration](#configuration)
- [Command-Line Options](#command-line-options)
- [Environment Variables](#environment-variables)
- [Project Layout](#project-layout)

## Support Status

| Area | Status | Notes |
| --- | --- | --- |
| TinyMCE | Primary support | Detects common TinyMCE iframe patterns and supports direct adapter operations. |
| CKEditor | Best-effort support | Detects common CKEditor iframe structures; behavior can vary by CKEditor version and site integration. |
| Quill | Best-effort support | Detects `.ql-editor` and attempts Quill-aware insertion where possible. |
| Generic `contenteditable` | Fallback support | Used when no known editor framework is detected. |
| Chrome | Primary browser support | Supports new sessions, headless mode, profiles, and existing sessions through remote debugging. |
| Firefox | New-session support | New Firefox sessions and headless mode are supported; attaching to an already-running Firefox session is not reliably supported yet. |
| Microsoft Edge | Supported | Chromium-based Edge provider. Supports new sessions, headless mode, profiles, and existing Edge sessions through remote debugging. |
| RemoteWebDriver / Selenium Grid | Supported | Uses a remote WebDriver endpoint such as Selenium Grid or browser containers. |
| Headless mode | Supported | Available for new local browser sessions and remote sessions; not supported with `--use-existing`. |
| Platform diagnostics | Supported | Reports OS, architecture, display server, container hints, browser availability, clipboard backend, headless recommendation, and remote port reachability. |
| Clipboard insertion | Best-effort support | Depends on `pyperclip`, operating-system clipboard utilities, browser focus, and site paste handling. |
| Direct HTML insertion | Fast but limited | Performs DOM/editor API insertion, not human typing. |
| Character typing | Compatibility-oriented | Can use Selenium `send_keys()` for real keystroke simulation. |
| Batch insertion | Performance-oriented | Inserts text in chunks and saves progress per batch. |
| Session resume | Stronger validation | Resume validates content hash, URL, offset, insertion strategy, and editor identity. |
| Encrypted sessions | Supported | Uses `cryptography` with Fernet and PBKDF2-HMAC-SHA256, with a random salt per encrypted session. |
| Verification | Structured support | Supports exact text, normalized text, and HTML comparison modes. |
| JSON output | Supported | Produces structured output for scripts and automation. |
| Diagnostics | Supported | Browser/platform, clipboard, editor, file, and session diagnostics are available. |

## Features

- Rich text editor detection through adapters:
  - TinyMCE
  - CKEditor
  - Quill
  - generic `contenteditable`
- Browser provider architecture:
  - Chrome provider
  - Firefox provider
  - Microsoft Edge provider
  - RemoteWebDriver provider
  - browser lifecycle manager
  - browser navigation service
  - browser validation diagnostics
  - platform/environment diagnostics
- Browser execution modes:
  - visible local browser
  - headless local browser
  - existing Chrome/Edge session through remote debugging
  - remote Selenium Grid/browser container
- Multiple insertion strategies:
  - clipboard
  - direct HTML / DOM insertion
  - real character typing with Selenium `send_keys()`
  - incremental DOM insertion
  - batch insertion
  - strategy fallback chain
- Content services:
  - UTF-8 file loading
  - multi-file loading
  - configurable separators
  - optional file headings
  - HTML sanitization
  - whitespace and paragraph formatting
  - SHA-256 content hashing
- Sessions:
  - JSON session store
  - resumable offset
  - content hash validation
  - URL validation
  - editor identity warning
  - insertion strategy warning
  - encrypted session support
- Verification:
  - exact text mode
  - normalized text mode
  - HTML mode
  - similarity threshold
  - first mismatch reporting
  - failure report artifacts
  - optional screenshot on verification failure
- Output:
  - terminal output
  - JSON output
  - silent or terminal progress reporting
- Diagnostics:
  - browser/platform diagnostics
  - clipboard diagnostics
  - editor diagnostics
  - content file diagnostics
  - session file diagnostics
- Config support:
  - CLI flags
  - environment variables
  - JSON, TOML, and YAML config files

## Safety and Limitations

### Direct DOM insertion limitations

Some strategies use direct DOM/editor API insertion. This is fast, but it is not always equivalent to real user typing.

Direct DOM insertion may fail to trigger:

- editor change events
- framework state updates
- autosave hooks
- dirty-state tracking
- validation logic
- undo history
- custom website event handlers

Always review inserted content before submitting a form.

If a website depends heavily on JavaScript framework state, direct DOM insertion can appear successful visually while the underlying form state remains unchanged.

Use `--strategy character --real-keystrokes` when you need behavior closest to real typing.

### Clipboard behavior

Clipboard insertion depends on:

- `pyperclip`
- operating-system clipboard utilities
- browser focus
- page permissions
- editor paste handling

On Linux, clipboard operations may require:

- X11: `xclip` or `xsel`
- Wayland: `wl-clipboard`

The clipboard strategy attempts to restore the previous clipboard value after success or failure, but clipboard behavior can still vary by platform and desktop environment.

### Browser profiles and authenticated sessions

Browser profiles are useful for sites that require login, but they carry risk. A browser profile can contain active sessions, cookies, saved logins, extensions, and personal browsing state.

Use browser profiles carefully:

- Prefer a dedicated automation browser profile.
- Avoid using your daily personal profile.
- Review the page manually before submission.
- Do not automate pages where accidental submission would cause harm.
- Avoid pages containing password fields or destructive actions.

Browser profiles are supported for local Chrome, Firefox, and Edge sessions. They are not supported with `--browser remote`.

### Existing browser sessions

Existing Chrome and Edge sessions can be used through remote debugging.

Existing Firefox sessions are not reliably supported by the current Firefox provider. Start a new Firefox session instead.

Headless mode cannot be used with `--use-existing`, because an already-running visible browser cannot be converted into headless mode.

### Headless mode

Headless mode starts the browser without a visible window. It is useful for CI, containers, remote servers, and repeatable automation.

Some websites behave differently in headless browsers, block automation more aggressively, or require visual/manual review before final submission.

For sensitive forms or authenticated pages, use visible browser mode first, confirm that insertion and verification behave correctly, then use headless mode only for repeatable trusted workflows.

### Remote browser sessions

Remote mode uses Selenium RemoteWebDriver. The browser runs in a remote Selenium Grid, Docker container, VPS, or other remote WebDriver service.

Remote mode does not support:

- `--use-existing`
- local browser profiles through `--profile`
- local browser remote debugging ports

Use remote browser/container capabilities instead.

### Verification limitations

Verification helps detect obvious insertion problems, but it cannot prove that a website saved or submitted the content correctly.

HTML verification can be affected by editor-generated markup. Normalized text verification can ignore formatting differences. Exact text verification is stricter but can fail due to harmless line-ending or whitespace differences.

### Resume limitations

Resume is refused when the source content hash changes. This prevents corrupt resumes where a saved offset points into different content.

Resume may warn when:

- URL mismatch is explicitly allowed
- source file path changed
- insertion strategy changed
- editor identity changed

Interactive mode can ask whether to continue through warnings. Non-interactive mode avoids unsafe warning resumes unless explicitly configured.

## Prerequisites

Install:

1. Python 3.12+
2. `uv`
3. At least one supported browser or a remote WebDriver endpoint:
   - Google Chrome
   - Mozilla Firefox
   - Microsoft Edge
   - Selenium Grid / RemoteWebDriver
4. Clipboard utilities when using clipboard mode on Linux:
   - X11: `xclip` or `xsel`
   - Wayland: `wl-clipboard`

The project dependencies include Selenium, WebDriver Manager, Pyperclip, and Cryptography.

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

### Linux, Ubuntu/Debian

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

For X11 alternative clipboard support:

```bash
sudo apt install -y xsel
```

For container/server usage, prefer `--headless` or `--browser remote`.

## Supported File Types

TinyMCE Typer reads UTF-8 text-based files.

Common supported inputs include:

- `.txt`
- `.md`
- `.markdown`
- `.html`
- `.htm`
- `.xml`
- `.json`
- `.csv`
- `.tsv`
- `.js`
- `.css`
- `.py`
- `.ts`
- `.tsx`
- `.jsx`
- other UTF-8 text/code files

Binary document formats such as `.docx`, `.pdf`, and rich `.rtf` are not parsed as document formats by the current content loader. Convert them to text/Markdown/HTML first.

## Usage

### Basic usage

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt
```

### Use Firefox

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser firefox
```

### Use Microsoft Edge

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser edge
```

### Run in headless mode

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --headless
```

Force visible mode when an environment/config file enables headless mode:

```bash
TINYMCE_TYPER_HEADLESS=true uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --headed
```

### Specify an iframe ID

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --iframe-id tinymce_ifr
```

### Specify an editor element ID

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --editor-id editor
```

### Choose one editor when multiple are detected

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --editor-index 2
```

### Use an authenticated browser profile

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --profile "/path/to/browser/profile"
```

Prefer a dedicated automation profile.

### Connect to an existing Chrome session

Start Chrome with remote debugging enabled:

```bash
google-chrome --remote-debugging-port=9222
```

Then connect the script:

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser chrome --use-existing --debugging-port 9222
```

### Connect to an existing Edge session

Start Edge with remote debugging enabled:

```bash
microsoft-edge --remote-debugging-port=9222
```

On Windows, the command may be:

```powershell
msedge.exe --remote-debugging-port=9222
```

Then connect the script:

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser edge --use-existing --debugging-port 9222
```

By default, existing browser mode does not navigate away from the current page unless forced.

Force navigation:

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt --browser chrome --use-existing --force-navigation
```

### Wait for a selector before editor detection

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --wait-selector ".tox-edit-area iframe"
```

### Multiple input files

```bash
uv run scripts/tinymce_typer.py https://example.com/editor first.md --files first.md second.md third.md
```

Use a custom separator:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor first.md --files first.md second.md --file-separator $'\n\n---\n\n'
```

Add headings before each file:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor first.md --files first.md second.md --include-file-headings
```

## Browser Providers

### Chrome

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --browser chrome
```

### Firefox

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --browser firefox
```

### Microsoft Edge

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --browser edge
```

### Remote

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt \
  --browser remote \
  --remote-webdriver-url http://localhost:4444/wd/hub \
  --remote-browser-name chrome
```

## RemoteWebDriver / Selenium Grid

Remote mode lets TinyMCE Typer run locally while the browser runs in Selenium Grid or a browser container.

Start a Selenium standalone Chrome container:

```bash
docker run --rm -p 4444:4444 selenium/standalone-chrome
```

Then run:

```bash
uv run scripts/tinymce_typer.py https://example.com/page-with-editor content.txt \
  --browser remote \
  --remote-webdriver-url http://localhost:4444/wd/hub \
  --remote-browser-name chrome
```

Remote browser names:

```text
chrome
firefox
edge
```

Remote mode is useful for:

- Docker
- CI
- VPS deployments
- Selenium Grid
- cloud browser workers

Remote mode does not support `--use-existing` or local browser profiles. Use remote browser/container capabilities instead.

Run remote diagnostics first:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt \
  --browser remote \
  --remote-webdriver-url http://localhost:4444/wd/hub \
  --remote-browser-name chrome \
  --diagnostics browser
```

## Insertion Strategies

Insertion behavior is implemented through strategy classes in:

```text
tinymce_typer/insertion/
```

Available strategies:

- `auto`
- `clipboard`
- `direct-html`
- `character`
- `batch`

### Auto strategy

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --strategy auto
```

`auto` builds a fallback chain based on config.

Typical order:

1. clipboard, unless disabled
2. batch, when `--batch` is enabled
3. direct HTML, when `--formatted` is enabled
4. character typing
5. direct HTML fallback

### Clipboard strategy

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --strategy clipboard
```

Clipboard insertion uses the system clipboard and paste shortcut.

Disable clipboard entirely:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --no-clipboard
```

### Direct HTML strategy

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.html --strategy direct-html --formatted
```

Direct HTML insertion is DOM/editor API insertion. It is not real typing.

### Character strategy

Real keystroke simulation:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --strategy character --real-keystrokes
```

Incremental DOM insertion instead of real keystrokes:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --strategy character --dom-incremental
```

### Batch strategy

```bash
uv run scripts/tinymce_typer.py https://example.com/editor large_content.txt --strategy batch --batch-size 100 --batch-delay 0.05
```

Batch mode inserts content in chunks and emits progress/session updates per batch.

## Sessions and Resume Safety

Session behavior lives in:

```text
tinymce_typer/sessions/
```

Sessions include:

- URL
- source file path
- content hash
- insertion strategy
- editor kind
- editor identifier
- progress offset
- current file
- completion state

### Resume

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --resume
```

### Refuse resume

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --no-resume
```

### Reset saved session

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --reset
```

### Disable sessions

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --no-session
```

### Custom session file

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --session-file .sessions/my-session.json
```

### Allow URL mismatch during resume

By default, resume is refused when the saved session URL differs from the current URL.

Allow URL mismatch:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --resume --force-resume-url
```

### Encrypted sessions

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --encrypt
```

Encrypted sessions use `cryptography` with Fernet and PBKDF2-HMAC-SHA256.

Each encrypted session uses a random salt stored with the encrypted payload.

Invalid passwords are refused. The tool does not silently fall back to raw session data after decryption failure.

## Verification

Available modes:

- `normalized-text`
- `exact-text`
- `html`

### Normalized text verification

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-mode normalized-text
```

This mode normalizes line endings and whitespace before comparison.

### Exact text verification

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-mode exact-text
```

This mode compares text more strictly.

### HTML verification

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.html --formatted --verification-mode html
```

This mode compares expected formatted HTML against actual editor HTML.

### Disable verification

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --no-verification
```

### Similarity threshold

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-threshold 0.95
```

The threshold must be between `0` and `1`.

### Failure reports

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-report
```

Reports include:

- pass/fail status
- mode
- similarity score
- threshold
- expected length
- actual length
- first mismatch details
- current URL
- editor type
- editor identifier
- actual editor HTML artifact path

### Screenshot on verification failure

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-report --screenshot-on-verification-failure
```

Use a custom report directory:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --verification-report-dir diagnostics/my-run
```

## Progress Reporting

Available reporters:

- terminal
- silent

Terminal progress is intended for humans. Silent progress is used for JSON/scripted output or quiet runs.

Disable progress output:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --quiet-progress
```

## JSON Output

Use JSON output when scripting:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --json
```

JSON mode automatically silences progress output so stdout remains machine-readable.

JSON output includes:

- success/failure
- duration
- editor type
- editor identifier
- strategy used
- content length
- inserted characters
- final offset
- verification result
- session file
- artifacts
- errors
- metadata

Example shape:

```json
{
  "success": true,
  "duration_seconds": 4.128,
  "editor_type": "tinymce",
  "editor_identifier": "iframe:tinymce_ifr",
  "strategy_used": "clipboard",
  "content_length": 1250,
  "inserted_characters": 1250,
  "final_offset": 1250,
  "message": "Inserted content using system clipboard paste.",
  "verification": {
    "passed": true,
    "mode": "normalized-text",
    "similarity": 0.998,
    "threshold": 0.9
  }
}
```

## Diagnostics

Run diagnostics instead of content insertion:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --diagnostics all
```

Available diagnostics modes:

- `all`
- `browser`
- `clipboard`
- `editor`
- `file`
- `session`

Examples:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --diagnostics browser
```

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --diagnostics clipboard
```

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --diagnostics session
```

Note: the current CLI still requires the positional `url` and `file` arguments even for diagnostics.

### Platform diagnostics

Browser diagnostics include platform/environment checks:

- operating system
- OS release/version
- architecture
- machine/processor
- Python version
- Linux display server: X11, Wayland, or none
- Docker/container hints
- headless-mode recommendation
- Chrome availability
- Firefox availability
- Edge availability
- configured browser availability
- remote debugging port reachability when using `--use-existing`
- RemoteWebDriver endpoint reachability when using `--browser remote`
- clipboard backend hints

Example:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt \
  --browser remote \
  --remote-webdriver-url http://localhost:4444/wd/hub \
  --diagnostics browser
```

Expected diagnostic categories include:

```text
platform
display_server
container
headless_mode
clipboard_backend
browser_matrix
browser_validation
configured_browser
remote_webdriver_port
```

On Linux, if no display server is detected, use `--headless` or provide X11/Wayland display access.

## Configuration

The tool can read configuration from:

1. environment variables
2. optional config file
3. CLI arguments

Supported config file formats:

- `.json`
- `.toml`
- `.yaml`
- `.yml`

Example JSON config:

```json
{
  "browser": "remote",
  "headless": true,
  "remote_webdriver_url": "http://localhost:4444/wd/hub",
  "remote_browser_name": "chrome",
  "iframe_id": "tinymce_ifr",
  "strategy": "auto",
  "formatted": false,
  "batch": false,
  "session_file": "tinymce_session.json",
  "verification_mode": "normalized-text",
  "verification_threshold": 0.9,
  "output_mode": "terminal"
}
```

Use a config file:

```bash
uv run scripts/tinymce_typer.py https://example.com/editor content.txt --config tinymce-typer.json
```

## Command-Line Options

### Required arguments

| Argument | Description |
| --- | --- |
| `url` | URL of the page containing the editor |
| `file` | Path to the main content file |

### Browser options

| Option | Description |
| --- | --- |
| `--browser {chrome,firefox,edge,remote}` | Browser provider to use. Default: `chrome` |
| `--headless` | Run the browser without a visible window. Useful for CI, containers, and servers |
| `--headed` | Force visible browser mode, overriding `TINYMCE_TYPER_HEADLESS=true` |
| `--profile PROFILE` | Path to local browser profile directory |
| `--use-existing` | Attach to an existing Chrome/Edge browser session through remote debugging |
| `--debugging-port PORT` | Chrome/Edge remote debugging port. Default: `9222` |
| `--marionette-port PORT` | Firefox Marionette port placeholder |
| `--remote-webdriver-url URL` | Remote WebDriver endpoint used when `--browser remote` |
| `--remote-browser-name {chrome,firefox,edge}` | Browser requested from the remote WebDriver provider. Default: `chrome` |
| `--force-navigation` | Navigate to the target URL even when using an existing browser |
| `--close-on-complete` | Close the browser after completion |
| `--keep-open`, `--keep-browser-open` | Keep the browser open after completion |
| `--detach` | Detach from browser session without closing |
| `--browser-wait-timeout SECONDS` | Time to keep browser open before closing; `0` waits until interrupted |
| `--implicit-wait SECONDS` | Selenium implicit wait. Default: `10` |

### Editor location options

| Option | Description |
| --- | --- |
| `--iframe-id IFRAME_ID` | ID of the iframe containing the editor |
| `--editor-id EDITOR_ID` | ID of the editor element |
| `--detect-multiple` | Detect multiple editors and require explicit selection behavior |
| `--editor-index INDEX` | 1-based editor index when multiple editors are detected |
| `--wait-selector SELECTOR` | CSS selector to wait for before editor detection |

### Content insertion options

| Option | Description |
| --- | --- |
| `--type-delay SECONDS` | Delay between character insertions. Default: `0.01` |
| `--formatted` | Treat source content as HTML and preserve formatting |
| `--no-clipboard` | Disable clipboard insertion |
| `--batch` | Enable batch insertion in auto mode |
| `--batch-size SIZE` | Characters per batch. Default: `50` |
| `--batch-delay SECONDS` | Delay between batches. Default: `0.1` |
| `--strategy {auto,clipboard,direct-html,character,batch}` | Insertion strategy. Default: `auto` |
| `--real-keystrokes` | Use Selenium `send_keys()` for character strategy |
| `--dom-incremental` | Use incremental DOM insertion instead of real keystrokes |

### Multi-file options

| Option | Description |
| --- | --- |
| `--files FILE [FILE ...]` | Multiple content files to insert sequentially |
| `--file-separator TEXT` | Separator between multiple files |
| `--include-file-headings` | Add a heading before each file when merging |

### Session options

| Option | Description |
| --- | --- |
| `--no-session` | Disable session saving/loading |
| `--reset` | Delete saved session before running |
| `--resume` | Resume saved progress without asking |
| `--no-resume` | Do not resume saved progress |
| `--encrypt` | Encrypt session data with a password |
| `--session-file FILE` | Session file path. Default: `tinymce_session.json` |
| `--force-resume-url` | Allow resume when saved URL differs from current URL |

### Verification options

| Option | Description |
| --- | --- |
| `--no-verification` | Disable verification |
| `--verification-mode {normalized-text,exact-text,html}` | Verification mode |
| `--verification-threshold FLOAT` | Minimum similarity threshold |
| `--verification-report` | Write verification report on failure |
| `--verification-report-dir DIR` | Directory for verification artifacts |
| `--screenshot-on-verification-failure` | Save browser screenshot when verification fails |

### Output and logging options

| Option | Description |
| --- | --- |
| `--json` | Write final output as JSON |
| `--output-mode {terminal,json}` | Final output format |
| `--quiet-progress` | Disable progress output |
| `--log-level LEVEL` | CRITICAL, ERROR, WARNING, INFO, or DEBUG |
| `--log-file FILE` | Optional detailed log file |
| `--verbose` | Enable debug-level console logs |
| `--quiet` | Only show errors |

### CLI behavior and diagnostics

| Option | Description |
| --- | --- |
| `--yes` | Automatically answer yes to safe prompts |
| `--non-interactive` | Run without interactive prompts |
| `--diagnostics {all,browser,clipboard,editor,file,session}` | Run diagnostics instead of insertion |

## Environment Variables

Environment variables use the `TINYMCE_TYPER_` prefix.

### Browser

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_BROWSER` | `chrome` | Browser provider: `chrome`, `firefox`, `edge`, or `remote` |
| `TINYMCE_TYPER_HEADLESS` | `false` | Run browser without a visible window |
| `TINYMCE_TYPER_BROWSER_PROFILE` | empty | Local browser profile path |
| `TINYMCE_TYPER_USE_EXISTING` | `false` | Attach to existing Chrome/Edge browser session |
| `TINYMCE_TYPER_DEBUGGING_PORT` | `9222` | Chrome/Edge remote debugging port |
| `TINYMCE_TYPER_MARIONETTE_PORT` | empty | Firefox Marionette port placeholder |
| `TINYMCE_TYPER_REMOTE_WEBDRIVER_URL` | empty | Remote WebDriver endpoint used when `TINYMCE_TYPER_BROWSER=remote` |
| `TINYMCE_TYPER_REMOTE_BROWSER_NAME` | `chrome` | Remote browser requested from Selenium Grid: `chrome`, `firefox`, or `edge` |
| `TINYMCE_TYPER_FORCE_NAVIGATION` | `false` | Navigate even when using an existing browser session |
| `TINYMCE_TYPER_CLOSE_ON_COMPLETE` | `false` | Close browser after successful completion |
| `TINYMCE_TYPER_KEEP_BROWSER_OPEN` | `true` | Keep browser open after completion |
| `TINYMCE_TYPER_DETACH` | `false` | Detach from browser without closing |
| `TINYMCE_TYPER_BROWSER_WAIT_TIMEOUT_SECONDS` | `0` | Seconds to keep browser open before closing |
| `TINYMCE_TYPER_IMPLICIT_WAIT_SECONDS` | `10` | Selenium implicit wait |

### Editor

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_IFRAME_ID` | empty | Iframe ID containing the editor |
| `TINYMCE_TYPER_EDITOR_ID` | empty | Editor element ID |
| `TINYMCE_TYPER_DETECT_MULTIPLE` | `false` | Detect and select from multiple editors |
| `TINYMCE_TYPER_EDITOR_INDEX` | empty | 1-based editor index |
| `TINYMCE_TYPER_WAIT_SELECTOR` | empty | CSS selector to wait for before editor detection |

### Insertion

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_TYPE_DELAY` | `0.01` | Delay between character insertions |
| `TINYMCE_TYPER_FORMATTED` | `false` | Treat content as HTML |
| `TINYMCE_TYPER_NO_CLIPBOARD` | `false` | Disable clipboard strategy |
| `TINYMCE_TYPER_BATCH` | `false` | Enable batch insertion |
| `TINYMCE_TYPER_BATCH_SIZE` | `50` | Characters per batch |
| `TINYMCE_TYPER_BATCH_DELAY` | `0.1` | Delay between batches |
| `TINYMCE_TYPER_STRATEGY` | `auto` | Strategy: `auto`, `clipboard`, `direct-html`, `character`, or `batch` |
| `TINYMCE_TYPER_REAL_KEYSTROKES` | `true` | Use Selenium `send_keys()` for character strategy |

### Sessions

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_NO_SESSION` | `false` | Disable sessions |
| `TINYMCE_TYPER_RESET` | `false` | Delete previous session |
| `TINYMCE_TYPER_RESUME` | `false` | Resume without asking |
| `TINYMCE_TYPER_NO_RESUME` | `false` | Do not resume |
| `TINYMCE_TYPER_ENCRYPT_SESSION` | `false` | Encrypt session data |
| `TINYMCE_TYPER_SESSION_FILE` | `tinymce_session.json` | Session file path |
| `TINYMCE_TYPER_FORCE_RESUME_URL` | `false` | Allow URL mismatch during resume |

### Verifications

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_NO_VERIFICATION` | `false` | Disable verification |
| `TINYMCE_TYPER_VERIFICATION_MODE` | `normalized-text` | Verification mode |
| `TINYMCE_TYPER_VERIFICATION_THRESHOLD` | `0.90` | Similarity threshold |
| `TINYMCE_TYPER_VERIFICATION_REPORT` | `false` | Write verification report on failure |
| `TINYMCE_TYPER_VERIFICATION_REPORT_DIR` | `diagnostics/verification` | Verification artifacts directory |
| `TINYMCE_TYPER_SCREENSHOT_ON_VERIFICATION_FAILURE` | `false` | Save screenshot on verification failure |

### Output, logging, and CLI behavior

| Variable | Default | Description |
| --- | --- | --- |
| `TINYMCE_TYPER_JSON` | `false` | Emit final output as JSON |
| `TINYMCE_TYPER_OUTPUT_MODE` | `terminal` | Final output mode |
| `TINYMCE_TYPER_QUIET_PROGRESS` | `false` | Disable progress output |
| `TINYMCE_TYPER_LOG_LEVEL` | `INFO` | Logging level |
| `TINYMCE_TYPER_LOG_FILE` | empty | Log file path |
| `TINYMCE_TYPER_VERBOSE` | `false` | Enable verbose logs |
| `TINYMCE_TYPER_QUIET` | `false` | Only show errors |
| `TINYMCE_TYPER_YES` | `false` | Automatically answer yes to safe prompts |
| `TINYMCE_TYPER_NON_INTERACTIVE` | `false` | Disable interactive prompts |
| `TINYMCE_TYPER_DIAGNOSTICS` | empty | Diagnostics mode |

## Project Layout

```text
tinymce_typer/
├── content.txt
├── LICENSE
├── pyproject.toml
├── README.md
├── scripts/
│   └── tinymce_typer.py
├── tinymce_typer/
│   ├── app/
│   ├── browser/
│   ├── cli/
│   ├── config/
│   ├── content/
│   ├── contracts/
│   ├── diagnostics/
│   ├── editors/
│   ├── insertion/
│   ├── logging/
│   ├── output/
│   ├── progress/
│   ├── sessions/
│   ├── verification/
│   ├── exceptions.py
│   └── __init__.py
└── uv.lock
```

[Back to Top](#tinymce-typer)
