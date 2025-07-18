import os
import time
import json
import argparse
import pyperclip
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Optional encryption support
ENCRYPTION_AVAILABLE = False
try:
    import base64
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    ENCRYPTION_AVAILABLE = True
except ImportError:
    # Provide more informative message about missing dependencies
    print("Note: Encryption features will be disabled. To enable encryption, install the cryptography package:")
    print("pip install cryptography")

class TinyMCETyper:
    def __init__(self, args):
        """
        Initialize the TinyMCE Typer with command line arguments.
        Sets up basic variables needed for tracking progress and state.
        
        Args:
            args: Command line arguments parsed from argparse
        """
        self.args = args
        self.driver = None                          # Will hold the WebDriver instance
        self.session_file = "tinymce_session.json"  # File to save/load progress
        self.progress = 0                           # Current typing progress (characters typed)
        self.editor_found = False                   # Flag to track if editor was successfully located
        self.content = ""                           # Will store the content to be typed
        self.start_time = None                      # For calculating typing speed and ETA

    def setup_browser(self):
        """Set up and return the selected browser driver.
        
        If use_existing flag is set, it will attempt to connect to an existing
        browser session rather than starting a new one.
        """
        try:
            if self.args.use_existing:
                print(f"Connecting to existing {self.args.browser} browser session...")
                return self.connect_to_existing_browser()
            else:
                print(f"Setting up new {self.args.browser} browser...")
                if self.args.browser == 'chrome':
                    options = webdriver.ChromeOptions()
                    options.add_argument('--start-maximized')
                    
                    # Profile support
                    if self.args.profile:
                        print(f"Using Chrome profile from: {self.args.profile}")
                        options.add_argument(f"--user-data-dir={self.args.profile}")
                    
                    # Initialization for newer Selenium versions
                    self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
                else:  # firefox
                    options = webdriver.FirefoxOptions()
                    
                    # Profile support
                    if self.args.profile:
                        print(f"Using Firefox profile from: {self.args.profile}")
                        options.add_argument("-profile")
                        options.add_argument(self.args.profile)
                    
                    # Initialization for newer Selenium versions
                    self.driver = webdriver.Firefox(service=webdriver.firefox.service.Service(GeckoDriverManager().install()), options=options)
                
                self.driver.implicitly_wait(10)
                return True
        except WebDriverException as e:
            print(f"Error setting up browser: {e}")
            print("Please make sure the browser is installed correctly.")
            return False

    def connect_to_existing_browser(self):
        """Connect to an existing browser session using remote debugging.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            if self.args.browser == 'chrome':
                # Check if debugging port is provided
                if not self.args.debugging_port:
                    print("Error: --debugging-port is required when using --use-existing with Chrome")
                    print("Example: Start Chrome with: chrome.exe --remote-debugging-port=9222")
                    print("Then use: --use-existing --debugging-port=9222")
                    return False
                
                options = webdriver.ChromeOptions()
                options.add_experimental_option("debuggerAddress", f"localhost:{self.args.debugging_port}")
                
                try:
                    # Connect to the existing Chrome instance
                    self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
                    
                    # Verify connection by checking browser state
                    self.driver.execute_script("return document.readyState")
                    print(f"Successfully connected to existing Chrome browser on port {self.args.debugging_port}")
                    
                    # Verify connection by checking current URL
                    current_url = self.driver.current_url
                    print(f"Connected to browser - current URL: {current_url}")
                    
                    return True
                except WebDriverException as e:
                    if "disconnected" in str(e).lower():
                        print("Error: Browser connection was lost. Is Chrome still running?")
                    elif "session" in str(e).lower():
                        print("Error: Invalid session. Chrome might have been restarted.")
                    else:
                        print(f"Connection error: {e}")
                        
                    print("\nMake sure Chrome is running with remote debugging enabled:")
                    print("1. Close all Chrome instances")
                    print(f"2. Start Chrome with: chrome.exe --remote-debugging-port={self.args.debugging_port}")
                    print("3. Then run this script again")
                    return False
            
            elif self.args.browser == 'firefox':
                # Firefox requires a different approach using Firefox's remote debugging
                print("Connecting to existing Firefox session...")
                print("Note: Firefox connection to existing session is experimental")
                
                if not self.args.debugging_port and not self.args.marionette_port:
                    print("Error: Either --debugging-port or --marionette-port is required for Firefox")
                    print("Example: --use-existing --marionette-port=2828")
                    return False
                
                port = self.args.marionette_port or self.args.debugging_port
                
                options = webdriver.FirefoxOptions()
                options.add_argument("-marionette")
                
                try:
                    # Connect to the Firefox Remote instance
                    from selenium.webdriver.firefox.remote_connection import FirefoxRemoteConnection
                    connection = FirefoxRemoteConnection(f"http://localhost:{port}")
                    self.driver = webdriver.Firefox(
                        service=webdriver.firefox.service.Service(GeckoDriverManager().install()), 
                        options=options,
                        command_executor=connection
                    )
                    
                    # Verify connection
                    self.driver.execute_script("return document.readyState")
                    print(f"Connected to existing Firefox browser on port {port}")
                    return True
                except Exception as e:
                    print(f"Failed to connect to existing Firefox browser: {e}")
                    print("\nFirefox connection requires the browser to be started with remote control enabled")
                    print("Please see Firefox documentation for enabling remote debugging or Marionette")
                    return False
            
            else:
                print(f"Error: Browser {self.args.browser} does not support existing session connection")
                return False
                    
        except Exception as e:
            print(f"Critical connection error: {type(e).__name__}: {e}")
            return False

    def load_content_from_file(self):
        """
        Load the content to be typed from the specified file.
        
        Returns:
            bool: True if file was successfully loaded, False otherwise
        """
        try:
            # Open and read the file with UTF-8 encoding to support special characters
            with open(self.args.file, 'r', encoding='utf-8') as file:
                self.content = file.read()
            print(f"Successfully loaded content from {self.args.file}")
            return True
        except FileNotFoundError:
            print(f"Error: File not found at {self.args.file}")
            return False
        except IOError as e:
            print(f"Error reading file: {e}")
            return False

    def load_multiple_files(self):
        """Load content from multiple files if specified.
        
        Returns:
            bool: True if loading was successful, False otherwise
        """
        if not self.args.files:
            # Fall back to single file
            return self.load_content_from_file()
        
        try:
            contents = []
            total_size = 0
            
            for file_path in self.args.files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_content = file.read()
                        contents.append(file_content)
                        total_size += len(file_content)
                    print(f"Successfully loaded content from {file_path} ({len(file_content)} characters)")
                except FileNotFoundError:
                    print(f"Error: File not found at {file_path}")
                    return False
                except IOError as e:
                    print(f"Error reading file {file_path}: {e}")
                    return False
            
            print(f"Total content size: {total_size} characters from {len(contents)} files")
            
            # Combine all content with optional separator
            separator = self.args.file_separator if hasattr(self.args, 'file_separator') else "\n\n"
            self.content = separator.join(contents)
            
            return True
        except Exception as e:
            print(f"Error loading multiple files: {e}")
            return False

    def find_and_focus_editor(self):
        """
        Find and focus the TinyMCE editor on the page using multiple detection methods.
        Handles different TinyMCE versions and configurations.
        
        Returns:
            WebElement or None: The editor element if found, None otherwise
        """
        try:
            print("Searching for TinyMCE editor...")
            
            # Method 0: If iframe ID is provided, switch to it first
            if self.args.iframe_id:
                try:
                    # Wait for iframe to be present and switch to it
                    iframe = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, self.args.iframe_id))
                    )
                    self.driver.switch_to.frame(iframe)
                    print(f"Switched to iframe with ID: {self.args.iframe_id}")
                except TimeoutException:
                    print(f"Warning: Could not find iframe with ID '{self.args.iframe_id}'")
                    print("Attempting to find TinyMCE without switching iframe...")
            
            # Variable to store the editor once found
            editor = None
            
            # Method 1: Use direct editor ID if provided
            if self.args.editor_id:
                try:
                    # Wait for editor to be clickable using provided ID
                    editor = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, self.args.editor_id))
                    )
                    print(f"Found editor with ID: {self.args.editor_id}")
                except TimeoutException:
                    print(f"Warning: Could not find editor with ID '{self.args.editor_id}'")
            
            # Method 2: Try common TinyMCE selectors
            if not editor:
                try:
                    # List of common TinyMCE element selectors for different versions
                    possible_selectors = [
                        "div.tox-edit-area__iframe",  # Modern TinyMCE
                        "iframe#tinymce_ifr",         # Common TinyMCE iframe
                        "iframe[id$='_ifr']",         # Any iframe ending with _ifr
                        "div.mce-edit-area iframe"    # Older TinyMCE
                    ]
                    
                    # Try each selector until we find a match
                    for selector in possible_selectors:
                        try:
                            iframe_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            self.driver.switch_to.frame(iframe_element)
                            editor = self.driver.find_element(By.CSS_SELECTOR, "body")
                            print(f"Found TinyMCE using selector: {selector}")
                            break
                        except (NoSuchElementException, WebDriverException):
                            continue  # Try next selector if this one fails
                except Exception as e:
                    print(f"Error while searching for TinyMCE elements: {e}")
            
            # Method 3: Last resort - look for any contenteditable element
            if not editor:
                try:
                    editor = self.driver.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
                    print("Found contenteditable element")
                except NoSuchElementException:
                    pass
            
            # If no editor was found, provide troubleshooting tips
            if not editor:
                print("Error: Could not find TinyMCE editor on the page.")
                print("Tips:")
                print("1. Make sure the page has fully loaded")
                print("2. Try providing the iframe ID with --iframe-id")
                print("3. Try providing the editor ID with --editor-id")
                print("4. Check if the editor is in an iframe structure")
                return None
            
            # Focus the editor using JavaScript
            self.driver.execute_script("arguments[0].focus();", editor)
            print("Successfully focused on the editor")
            self.editor_found = True
            return editor
        
        except Exception as e:
            print(f"Unexpected error while finding editor: {e}")
            return None

    def find_editor(self):
        """Find various types of rich text editors.
        
        Returns:
            list: List of tuples (editor_type, editor_element, frame_element) for each found editor
        """
        editors = []
        original_window = self.driver.current_window_handle
        
        # Start from main frame
        try:
            self.driver.switch_to.default_content()
        except:
            pass
        
        # Try TinyMCE
        try:
            # Check for common TinyMCE elements
            possible_selectors = [
                "div.tox-edit-area__iframe",  # Modern TinyMCE
                "iframe#tinymce_ifr",         # Common TinyMCE iframe
                "iframe[id$='_ifr']",         # Any iframe ending with _ifr
                "div.mce-edit-area iframe"    # Older TinyMCE
            ]
            
            for selector in possible_selectors:
                try:
                    iframe_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for iframe in iframe_elements:
                        try:
                            iframe_id = iframe.get_attribute("id") or "unknown"
                            self.driver.switch_to.frame(iframe)
                            editor = self.driver.find_element(By.CSS_SELECTOR, "body")
                            editors.append((f"TinyMCE ({iframe_id})", editor, iframe))
                            self.driver.switch_to.default_content()
                        except:
                            self.driver.switch_to.default_content()
                except:
                    continue
        except Exception as e:
            print(f"Error while searching for TinyMCE: {e}")
            self.driver.switch_to.default_content()
        
        # Try CKEditor
        try:
            ckeditor_frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe.cke_wysiwyg_frame")
            for frame in ckeditor_frames:
                try:
                    frame_id = frame.get_attribute("id") or "unknown"
                    self.driver.switch_to.frame(frame)
                    editor = self.driver.find_element(By.CSS_SELECTOR, "body")
                    editors.append((f"CKEditor ({frame_id})", editor, frame))
                    self.driver.switch_to.default_content()
                except:
                    self.driver.switch_to.default_content()
        except Exception as e:
            print(f"Error while searching for CKEditor: {e}")
            self.driver.switch_to.default_content()
            
        # Try Quill editor
        try:
            quill_editors = self.driver.find_elements(By.CSS_SELECTOR, ".ql-editor")
            for idx, editor in enumerate(quill_editors):
                editors.append((f"Quill Editor ({idx+1})", editor, None))
        except Exception as e:
            print(f"Error while searching for Quill Editor: {e}")
        
        # Try generic contenteditable elements
        try:
            content_editables = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
            for idx, editor in enumerate(content_editables):
                # Skip if already found in another editor type
                if not any(editor == e[1] for e in editors):
                    tag_name = editor.tag_name
                    editors.append((f"ContentEditable {tag_name} ({idx+1})", editor, None))
        except Exception as e:
            print(f"Error while searching for contenteditable elements: {e}")
        
        # Return to original state
        try:
            self.driver.switch_to.window(original_window)
            self.driver.switch_to.default_content()
        except:
            pass
        
        return editors

    def try_clipboard_paste(self, editor):
        """
        Attempt to paste content using clipboard methods while preserving whitespace.
        Tries both direct HTML insertion and Ctrl+V methods.
        
        Args:
            editor: The editor WebElement to paste into
            
        Returns:
            bool: True if clipboard paste was successful, False otherwise
        """
        try:
            print("Attempting clipboard paste with whitespace preservation...")
            # Save original clipboard content to restore later
            original_clipboard = pyperclip.paste()
            
            # Format content with HTML to preserve whitespace
            formatted_content = self.content.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            
            # Method 1: Try direct HTML insertion (most reliable for whitespace)
            print("Trying direct HTML insertion...")
            self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, formatted_content)
            
            # Verify if content was inserted correctly
            time.sleep(0.5)
            editor_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
            if editor_content and len(editor_content) > 10:  # Basic check that something was inserted
                print("Direct HTML insertion successful!")
                return True
                
            # Method 2: Try Ctrl+V paste with formatted HTML
            print("Direct insertion failed. Trying Ctrl+V with HTML content...")
            editor.clear()
            pyperclip.copy(formatted_content)  # Copy the formatted content
            editor.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            
            # Check if paste worked
            editor_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
            if editor_content and len(editor_content) > 10:
                print("Ctrl+V paste with formatted HTML successful!")
                return True
                
            # Method 3: Try with plain text
            print("HTML methods failed. Trying with plain text...")
            editor.clear()
            pyperclip.copy(self.content)  # Copy original content
            editor.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            
            # Check if this method worked
            editor_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
            if editor_content and len(editor_content) > 10:
                print("Plain text paste successful!")
                # Now format the content for whitespace
                formatted_content = editor_content.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, formatted_content)
                return True
                
            # All paste methods failed
            print("All clipboard paste methods failed. Falling back to character typing.")
            editor.clear()
            # Restore original clipboard
            pyperclip.copy(original_clipboard)
            return False
                
        except Exception as e:
            print(f"Error with clipboard methods: {e}")
            try:
                # Attempt to restore original clipboard even if error occurred
                pyperclip.copy(original_clipboard)
            except:
                pass
            return False

    def type_formatted_content(self, editor, content):
        """
        Type content while preserving HTML formatting and whitespace.
        Uses direct innerHTML setting if HTML tags are detected.
        
        Args:
            editor: The editor WebElement to type into
            content: The content string to be typed
            
        Returns:
            bool: True if formatting and typing was successful, False otherwise
        """
        try:
            # Check if content appears to have HTML formatting by looking for common HTML tags
            if '<' in content and '>' in content and ('</p>' in content or '<br' in content or '<div' in content):
                print("Detected HTML formatting in content, preserving format...")
                # Use JavaScript to set innerHTML directly instead of typing character by character
                self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, content)
                return True
            else:
                # For non-HTML content, preserve whitespace by converting to HTML format
                print("Preserving whitespace and line breaks in plain text content...")
                # Replace newlines with <br> tags and preserve spaces
                formatted_content = content.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                
                # Use JavaScript to set innerHTML directly with whitespace preserved
                self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, formatted_content)
                return True
        except Exception as e:
            print(f"Error while handling formatted content: {e}")
            return False

    def type_content(self, editor, content):
        """
        Type the content into the editor character by character.
        Supports resuming from previous sessions and shows progress.
        
        Args:
            editor: The editor WebElement to type into
            content: The content string to be typed
            
        Returns:
            bool: True if typing was successful, False otherwise
        """
        try:
            print("\nStarting to type content...")
            print(f"Using typing delay of {self.args.type_delay} seconds between characters")
            
            # Resume from saved progress if available
            start_pos = self.progress
            if start_pos > 0:
                print(f"Resuming from previous session at character {start_pos}")
                
                # Get text already typed
                existing_text = content[:start_pos]
                # Get remaining text to type
                remaining_text = content[start_pos:]
                
                # Set existing text directly using JavaScript with whitespace preservation
                if len(existing_text) > 0:
                    # Replace newlines with <br> tags to preserve line breaks
                    formatted_existing = existing_text.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                    self.driver.execute_script(f"arguments[0].innerHTML = arguments[1];", editor, formatted_existing)
                    
                content = remaining_text
            else:
                # Clear existing content if any
                editor.clear()
            
            # Record start time for progress estimation
            self.start_time = time.time()
            
            # Type the content character by character with special handling for whitespace
            total_chars = len(content)
            current_html = ""
            
            for i, char in enumerate(content):
                current_pos = start_pos + i
                
                # Special handling for whitespace characters
                if char == '\n':
                    # Add a line break for newlines
                    current_html += '<br>'
                elif char == ' ' and content[i-1:i] == ' ':
                    # Use non-breaking space for consecutive spaces
                    current_html += '&nbsp;'
                else:
                    # Escape special characters for JavaScript
                    escaped_char = char.replace("'", "\\'").replace('"', '\\"')
                    current_html += escaped_char
                
                # Update the editor's content
                self.driver.execute_script(f"arguments[0].innerHTML = arguments[1];", editor, current_html)
                
                # Save progress periodically (every 100 characters)
                if current_pos % 100 == 0:
                    self.progress = current_pos
                    self.save_session()
                
                # Show progress updates (every 10 characters)
                if i % 10 == 0 or i == total_chars - 1:
                    self.show_progress(i, total_chars, start_pos)
                
                # Wait between characters to simulate typing
                time.sleep(self.args.type_delay)
            
            # Final progress update
            self.progress = start_pos + total_chars
            self.save_session()
            
            print("\nFinished typing content!")
            return True
        except Exception as e:
            print(f"\nError while typing content: {e}")
            self.save_session()  # Save session on error too
            return False

    def type_content_batched(self, editor, content):
        """Type content in small batches for better performance while preserving whitespace.
        
        Args:
            editor: The editor element
            content: The content to type
            
        Returns:
            bool: True if typing was successful, False otherwise
        """
        try:
            print("\nStarting to type content using batch insertion...")
            
            # Get batch size from args or use default
            batch_size = self.args.batch_size if hasattr(self.args, 'batch_size') else 50
            batch_delay = self.args.batch_delay if hasattr(self.args, 'batch_delay') else 0.1
            
            print(f"Using batch size of {batch_size} characters with {batch_delay}s delay between batches")
            
            # Resume from saved progress if available
            start_pos = self.progress
            if start_pos > 0:
                print(f"Resuming from previous session at character {start_pos}")
                existing_text = content[:start_pos]
                remaining_text = content[start_pos:]
                if len(existing_text) > 0:
                    # Format existing text with whitespace preservation
                    formatted_existing = existing_text.replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
                    self.driver.execute_script(f"arguments[0].innerHTML = arguments[1];", editor, formatted_existing)
                content = remaining_text
            else:
                editor.clear()
            
            # Record start time for progress estimation
            self.start_time = time.time()
            
            # Process and type the content in batches with whitespace preservation
            total_chars = len(content)
            current_html = self.driver.execute_script("return arguments[0].innerHTML;", editor) or ""
            
            for i in range(0, total_chars, batch_size):
                current_pos = start_pos + i
                end_pos = min(i + batch_size, total_chars)
                batch = content[i:end_pos]
                
                # Format the batch with whitespace preservation
                formatted_batch = ""
                for char in batch:
                    if char == '\n':
                        formatted_batch += '<br>'
                    elif char == ' ' and formatted_batch.endswith(' '):
                        formatted_batch += '&nbsp;'
                    else:
                        formatted_batch += char
                
                # Update current HTML content
                current_html += formatted_batch
                
                # Insert the formatted batch
                self.driver.execute_script("arguments[0].innerHTML = arguments[1];", editor, current_html)
                
                # Save progress periodically
                self.progress = current_pos + (end_pos - i)
                if self.progress % (batch_size * 5) == 0:
                    self.save_session()
                
                # Show progress
                self.show_progress(i + (end_pos - i), total_chars, start_pos)
                
                time.sleep(batch_delay)  # Shorter delay between batches
            
            # Final progress update
            self.progress = start_pos + total_chars
            self.save_session()
            
            print("\nFinished typing content!")
            return True
        except Exception as e:
            print(f"\nError while typing content in batches: {e}")
            self.save_session()  # Save session on error too
            return False

    def verify_typed_content(self, editor, expected_content):
        """Verify that the content was typed correctly.
        
        Args:
            editor: The editor element
            expected_content: The content that should have been typed
            
        Returns:
            bool: True if content verification passed, False otherwise
        """
        try:
            # Get the current content from the editor
            actual_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
            
            # Clean up whitespace for comparison
            expected_clean = ' '.join(expected_content.split())
            actual_clean = ' '.join(actual_content.split())
            
            # Check if the content matches
            if expected_clean in actual_clean:
                print("Content verification: SUCCESS")
                return True
            else:
                print("Content verification: FAILED")
                print("Content may not have been entered correctly")
                
                # Calculate similarity percentage
                import difflib
                similarity = difflib.SequenceMatcher(None, expected_clean, actual_clean).ratio() * 100
                print(f"Content similarity: {similarity:.1f}%")
                
                # If significant mismatch, offer retry
                if similarity < 90 and not self.args.no_verification:
                    response = input("Would you like to retry typing? (y/n): ")
                    return response.lower() != 'y'
                
                return False
        except Exception as e:
            print(f"Error during content verification: {e}")
            return False

    def show_progress(self, current, total, offset=0):
        """
        Display progress information and estimated time remaining.
        
        Args:
            current: Current character index
            total: Total number of characters
            offset: Starting position offset (for resumed sessions)
        """
        progress_pct = (current + 1) / total * 100
        
        # Calculate speed and ETA
        if self.start_time and current > 0:
            elapsed = time.time() - self.start_time
            chars_per_sec = current / elapsed if elapsed > 0 else 0
            remaining_chars = total - current
            remaining_time = remaining_chars / chars_per_sec if chars_per_sec > 0 else 0
            
            # Format remaining time in minutes and seconds
            remaining_mins = int(remaining_time // 60)
            remaining_secs = int(remaining_time % 60)
            eta = f"{remaining_mins}m {remaining_secs}s"
            
            # Print progress with speed and ETA information
            print(f"Progress: {progress_pct:.1f}% ({current+1}/{total} chars) | Speed: {chars_per_sec:.1f} chars/sec | ETA: {eta}", end='\r')
        else:
            # Simple progress display if timing info is not available
            print(f"Progress: {progress_pct:.1f}% ({current+1}/{total} chars)", end='\r')
            
    def get_encryption_key(self, password):
        """Generate an encryption key from password."""
        if not ENCRYPTION_AVAILABLE:
            return None
            
        try:
            # Use password to derive a key
            password_bytes = password.encode()
            salt = b'TinyMCETyperSalt'  # Fixed salt - could be made configurable
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            return key
        except Exception as e:
            print(f"Error generating encryption key: {e}")
            return None

    def encrypt_data(self, data, password):
        """Encrypt data using the provided password."""
        if not ENCRYPTION_AVAILABLE:
            print("Encryption not available. Install cryptography package to enable.")
            return data
            
        try:
            key = self.get_encryption_key(password)
            if not key:
                return data
                
            # Convert data to string if it's not already
            if isinstance(data, dict):
                data = json.dumps(data)
                
            # Encrypt the data
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"Encryption failed: {e}")
            return data

    def decrypt_data(self, encrypted_data, password):
        """Decrypt data using the provided password."""
        if not ENCRYPTION_AVAILABLE:
            print("Decryption not available. Install cryptography package to enable.")
            return encrypted_data
            
        try:
            key = self.get_encryption_key(password)
            if not key:
                return encrypted_data
                
            # Decrypt the data
            f = Fernet(key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data).decode()
            return decrypted_data
        except Exception as e:
            print(f"Decryption failed: {e}")
            return encrypted_data

    def save_session(self):
        """Save current session data to file with optional encryption."""
        try:
            session_data = {
                "url": self.args.url,
                "file": self.args.file,
                "progress": self.progress,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if encryption is requested and available
            if hasattr(self.args, 'encrypt') and self.args.encrypt:
                if ENCRYPTION_AVAILABLE:
                    if not hasattr(self, 'password'):
                        self.password = input("Enter password for session encryption: ")
                    
                    # Encrypt the session data
                    encrypted_data = self.encrypt_data(session_data, self.password)
                    
                    with open(self.session_file, 'w', encoding='utf-8') as f:
                        f.write(encrypted_data)
                    print("Session saved with encryption")
                else:
                    print("Warning: Encryption requested but not available. Session saved unencrypted.")
                    with open(self.session_file, 'w', encoding='utf-8') as f:
                        json.dump(session_data, f)
            else:
                # Save unencrypted
                with open(self.session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f)
        except Exception as e:
            print(f"Warning: Failed to save session: {e}")

    def load_session(self):
        """Load previous session data if available with optional decryption."""
        try:
            if os.path.exists(self.session_file):
                # Try to determine if file is encrypted by attempting to parse as JSON
                encrypted = False
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        session_data = json.loads(content)
                    except json.JSONDecodeError:
                        # File may be encrypted
                        encrypted = True
                
                if encrypted and ENCRYPTION_AVAILABLE:
                    if not hasattr(self, 'password'):
                        self.password = input("Session appears encrypted. Enter password to decrypt: ")
                    
                    # Decrypt the session data
                    with open(self.session_file, 'r', encoding='utf-8') as f:
                        encrypted_data = f.read()
                        
                    decrypted_data = self.decrypt_data(encrypted_data, self.password)
                    try:
                        session_data = json.loads(decrypted_data)
                        print("Session decrypted successfully")
                    except json.JSONDecodeError:
                        print("Decryption failed. Incorrect password or corrupted file.")
                        return
                elif encrypted and not ENCRYPTION_AVAILABLE:
                    print("Session appears encrypted but decryption support is not available.")
                    print("Install the cryptography package to enable decryption.")
                    return
                else:
                    # File is not encrypted
                    with open(self.session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                
                # Check if session is for the same URL and file
                if session_data["url"] == self.args.url and session_data["file"] == self.args.file:
                    self.progress = session_data["progress"]
                    print(f"Found saved session from {session_data['timestamp']}")
                    print(f"Progress: {self.progress} characters typed")
                    
                    if self.args.reset:
                        print("Reset flag provided, starting from beginning")
                        self.progress = 0
                    else:
                        response = input("Resume from saved progress? (y/n): ")
                        if response.lower() != 'y':
                            print("Starting from beginning")
                            self.progress = 0
        except Exception as e:
            print(f"Warning: Failed to load session: {e}")
            self.progress = 0

    def handle_multiple_editors(self):
        """
        Find and manage multiple TinyMCE editors on the page.
        Allows user to select which editor to use.
        
        Returns:
            WebElement or None: The selected editor element if found, None otherwise
        """
        try:
            print("Searching for multiple TinyMCE editors...")
            
            # Return to main frame if we're in an iframe
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            # Find all potential TinyMCE instances by looking for iframes with ID ending in '_ifr'
            tinymce_iframes = self.driver.find_elements(By.CSS_SELECTOR, "iframe[id$='_ifr']")
            
            # If no editors found, fall back to standard detection
            if not tinymce_iframes or len(tinymce_iframes) == 0:
                print("No multiple editors found, using standard editor detection")
                return self.find_and_focus_editor()
            
            print(f"Found {len(tinymce_iframes)} potential TinyMCE editors")
            
            # If only one editor, use standard method
            if len(tinymce_iframes) == 1:
                return self.find_and_focus_editor()
            
            # Multiple editors found - let user choose
            print("\nMultiple editors found. Please select which one to use:")
            for i, iframe in enumerate(tinymce_iframes):
                iframe_id = iframe.get_attribute("id")
                print(f"{i+1}. Editor in iframe: {iframe_id}")
            
            try:
                # Get user's choice
                choice = int(input("\nEnter editor number (or 0 to use standard detection): "))
                if choice == 0:
                    return self.find_and_focus_editor()
                elif 1 <= choice <= len(tinymce_iframes):
                    # Focus the selected editor
                    chosen_iframe = tinymce_iframes[choice-1]
                    self.driver.switch_to.frame(chosen_iframe)
                    editor = self.driver.find_element(By.CSS_SELECTOR, "body")
                    self.driver.execute_script("arguments[0].focus();", editor)
                    print(f"Successfully focused on editor {choice}")
                    self.editor_found = True
                    return editor
                else:
                    print("Invalid choice, using standard editor detection")
                    return self.find_and_focus_editor()
            except ValueError:
                print("Invalid input, using standard editor detection")
                return self.find_and_focus_editor()
                
        except Exception as e:
            print(f"Error detecting multiple editors: {e}")
            return self.find_and_focus_editor()

    def run(self):
        """Main execution method."""
        if not self.setup_browser():
            return False
        
        # Handle multiple files if specified, otherwise load single file
        if self.args.files:
            if not self.load_multiple_files():
                return False
        else:
            if not self.load_content_from_file():
                return False
        
        try:
            # Only navigate to URL if we're not using an existing session
            # or if the user explicitly requests it
            if not self.args.use_existing or self.args.force_navigation:
                print(f"Loading page: {self.args.url}")
                self.driver.get(self.args.url)
                print("Page loaded successfully")
            else:
                print("Using current page in existing browser session")
                print(f"Current URL: {self.driver.current_url}")
                
                # Ask user if they want to navigate to the specified URL
                if self.args.url != self.driver.current_url:
                    response = input(f"\nCurrent page differs from specified URL ({self.args.url}).\nNavigate to specified URL? (y/n): ")
                    if response.lower() == 'y':
                        print(f"Navigating to: {self.args.url}")
                        self.driver.get(self.args.url)
                        print("Page loaded successfully")
            
            # Load previous session if available
            if not self.args.no_session:
                self.load_session()
            
            # Wait for user to confirm the page is ready
            input("\nPress Enter when the page is fully loaded and you're ready to start typing...")
            
            # Check for and handle multiple editors if requested
            editor = None
            if self.args.detect_multiple:
                editor = self.handle_multiple_editors()
            else:
                # Find and focus the editor
                editor = self.find_and_focus_editor()
                
                # If standard method fails, try the new multi-editor finder
                if not editor:
                    editors = self.find_editor()
                    if editors:
                        print(f"Found {len(editors)} alternative editors")
                        if len(editors) == 1:
                            editor_type, editor, frame = editors[0]
                            if frame:
                                self.driver.switch_to.frame(frame)
                            print(f"Using {editor_type} editor")
                        else:
                            # Let user choose which editor to use
                            print("Multiple editors found. Please select:")
                            for idx, (editor_type, _, _) in enumerate(editors):
                                print(f"{idx+1}. {editor_type}")
                            try:
                                choice = int(input("Enter editor number: ")) - 1
                                if 0 <= choice < len(editors):
                                    editor_type, editor, frame = editors[choice]
                                    if frame:
                                        self.driver.switch_to.frame(frame)
                                    print(f"Using {editor_type} editor")
                                else:
                                    print("Invalid choice")
                            except ValueError:
                                print("Invalid input")
            
            if editor:
                success = False
                
                # Try clipboard method first if not disabled
                if not self.args.no_clipboard:
                    clipboard_success = self.try_clipboard_paste(editor)
                    if clipboard_success:
                        success = True
                
                # If clipboard failed or was disabled, try typing methods
                if not success:
                    if self.args.batch:
                        # Use batched typing for better performance
                        success = self.type_content_batched(editor, self.content)
                    elif self.args.formatted:
                        success = self.type_formatted_content(editor, self.content)
                    else:
                        success = self.type_content(editor, self.content)
                
                if success:
                    # Verify content if verification is not disabled
                    if not self.args.no_verification:
                        verification = self.verify_typed_content(editor, self.content)
                        if not verification:
                            print("Warning: Content verification failed")
                    
                    print("\nTyping completed successfully!")
                    print("You can now manually review and submit the form")
                    
                    # Don't close browser if we're using an existing session
                    if self.args.use_existing:
                        print("\nKeeping existing browser session open")
                        print("Script will now exit, browser will remain running")
                    else:
                        print("\nThe browser will remain open until you close this script")
                        print("Press Ctrl+C in this terminal to exit the script and close the browser")
                        
                        # Keep the script running until manually terminated
                        try:
                            while True:
                                time.sleep(1)
                        except KeyboardInterrupt:
                            print("\nScript terminated by user")
                else:
                    print("\nTyping process encountered errors")
            
        except KeyboardInterrupt:
            print("\nScript terminated by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            # Only quit the driver if we're not using an existing session
            if not self.args.use_existing:
                print("\nReminder: Press Ctrl+C to quit and close the browser")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nExiting and closing browser")
                    self.driver.quit()
            else:
                print("\nExiting while keeping browser session open")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Automate typing text into TinyMCE editor')
    
    # Required arguments
    parser.add_argument('url', help='URL of the page with TinyMCE editor')
    parser.add_argument('file', help='Path to the text file containing content to type')
    
    # Browser options
    parser.add_argument('--browser', choices=['chrome', 'firefox'], default='chrome',
                        help='Browser to use (default: chrome)')
    parser.add_argument('--profile', default='',
                        help='Path to browser profile directory')
    
    # Editor location options
    parser.add_argument('--iframe-id', default='', 
                        help='ID of the iframe containing TinyMCE (if applicable)')
    parser.add_argument('--editor-id', default='', 
                        help='ID of the TinyMCE editor element (if known)')
    parser.add_argument('--detect-multiple', action='store_true',
                        help='Detect and select from multiple TinyMCE editors')
    
    # Content insertion options
    parser.add_argument('--type-delay', type=float, default=0.01,
                        help='Delay between keystrokes in seconds (default: 0.01)')
    parser.add_argument('--formatted', action='store_true',
                        help='Preserve HTML formatting in the content')
    parser.add_argument('--no-clipboard', action='store_true',
                        help='Disable clipboard paste attempt')
    parser.add_argument('--batch', action='store_true',
                        help='Use batch insertion for better performance')
    parser.add_argument('--batch-size', type=int, default=50,
                        help='Number of characters to insert at once (default: 50)')
    parser.add_argument('--batch-delay', type=float, default=0.1,
                        help='Delay between batch insertions in seconds (default: 0.1)')
    
    # Session handling options
    parser.add_argument('--no-session', action='store_true',
                        help='Disable session saving/loading')
    parser.add_argument('--reset', action='store_true',
                        help='Reset progress from previous session')
    parser.add_argument('--encrypt', action='store_true',
                        help='Encrypt session data with a password')
    
    # Content verification options
    parser.add_argument('--no-verification', action='store_true',
                        help='Disable content verification after typing')
    
    # Existing browser support
    parser.add_argument('--use-existing', action='store_true',
                        help='Connect to an existing browser session instead of starting new one')
    parser.add_argument('--debugging-port', type=int, default=9222,
                        help='Port for remote debugging (default: 9222, used with --use-existing)')
    parser.add_argument('--marionette-port', type=int, default=None,
                        help='Port for Firefox Marionette (used with --use-existing for Firefox)')
    parser.add_argument('--force-navigation', action='store_true',
                        help='Force navigation to URL even when using existing browser')
    
    # Multi-file support
    parser.add_argument('--files', nargs='+', default=[],
                        help='Multiple content files to type sequentially')
    parser.add_argument('--file-separator', default='\n\n',
                        help='Separator to use between content from multiple files')
    
    return parser.parse_args()


# Main script entry point
if __name__ == "__main__":
    args = parse_arguments()
    
    print("\n========== TinyMCE Typer ==========")
    print("This script automates typing text into a TinyMCE editor")
    
    if args.use_existing:
        print("\nMode: Connecting to existing browser session")
        if args.browser == 'chrome':
            print(f"Make sure Chrome is running with: --remote-debugging-port={args.debugging_port}")
        elif args.browser == 'firefox':
            port = args.marionette_port or args.debugging_port
            print(f"Make sure Firefox has remote control enabled on port {port}")
    else:
        print("\nMode: Starting new browser session")
    
    print("Press Ctrl+C in this terminal to exit the script\n")
    
    typer = TinyMCETyper(args)
    typer.run()