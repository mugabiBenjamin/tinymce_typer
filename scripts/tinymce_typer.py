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

class TinyMCETyper:
    def __init__(self, args):
        """
        Initialize the TinyMCE Typer with command line arguments.
        Sets up basic variables needed for tracking progress and state.
        
        Args:
            args: Command line arguments parsed from argparse
        """
        self.args = args
        self.driver = None  # Will hold the WebDriver instance
        self.session_file = "tinymce_session.json"  # File to save/load progress
        self.progress = 0  # Current typing progress (characters typed)
        self.editor_found = False  # Flag to track if editor was successfully located
        self.content = ""  # Will store the content to be typed
        self.start_time = None  # For calculating typing speed and ETA
    
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
                    # Updated initialization for newer Selenium versions
                    self.driver = webdriver.Chrome(service=webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
                else:  # firefox
                    options = webdriver.FirefoxOptions()
                    # Updated initialization for newer Selenium versions
                    self.driver = webdriver.Firefox(service=webdriver.firefox.service.Service(GeckoDriverManager().install()), options=options)
                
                self.driver.implicitly_wait(10)
                return True
        except WebDriverException as e:
            print(f"Error setting up browser: {e}")
            print("Please make sure the browser is installed correctly.")
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

    def try_clipboard_paste(self, editor):
        """
        Attempt to paste content using clipboard methods.
        Tries both Ctrl+V and Shift+Insert methods.
        
        Args:
            editor: The editor WebElement to paste into
            
        Returns:
            bool: True if clipboard paste was successful, False otherwise
        """
        try:
            print("Attempting clipboard paste methods...")
            # Save original clipboard content to restore later
            original_clipboard = pyperclip.paste()
            
            # Try with a small test first to check if pasting works
            test_text = "Test paste functionality"
            pyperclip.copy(test_text)
            
            # Method 1: Try Ctrl+V paste
            print("Trying Ctrl+V paste method...")
            editor.send_keys(Keys.CONTROL, 'v')
            time.sleep(1)
            
            # Check if paste worked by examining editor content
            editor_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
            ctrl_v_success = test_text in editor_content
            
            # Method 2: If Ctrl+V failed, try Shift+Insert
            if not ctrl_v_success:
                print("Ctrl+V paste failed. Trying Shift+Insert method...")
                editor.clear()  # Clear any partial content
                pyperclip.copy(test_text)  # Ensure test text is in clipboard
                
                try:
                    # Try Shift+Insert paste
                    editor.send_keys(Keys.SHIFT, Keys.INSERT)
                    time.sleep(1)
                    
                    # Check if this method worked
                    editor_content = self.driver.execute_script("return arguments[0].innerHTML;", editor)
                    shift_insert_success = test_text in editor_content
                    
                    if shift_insert_success:
                        print("Shift+Insert paste works! Using this paste method...")
                    else:
                        print("Shift+Insert paste also failed.")
                except Exception as e:
                    print(f"Error with Shift+Insert method: {e}")
                    shift_insert_success = False
            else:
                # Ctrl+V worked, no need to try Shift+Insert
                shift_insert_success = False
                
            # If either method worked, use it for the full content
            if ctrl_v_success or shift_insert_success:
                paste_method = Keys.CONTROL + 'v' if ctrl_v_success else (Keys.SHIFT, Keys.INSERT)
                editor.clear()
                
                # Split content into chunks to avoid clipboard limitations
                chunk_size = 5000
                chunks = [self.content[i:i+chunk_size] for i in range(0, len(self.content), chunk_size)]
                
                # Paste each chunk separately
                for i, chunk in enumerate(chunks):
                    pyperclip.copy(chunk)
                    
                    # Use the method that worked in our test
                    if ctrl_v_success:
                        editor.send_keys(Keys.CONTROL, 'v')
                    else:
                        editor.send_keys(Keys.SHIFT, Keys.INSERT)
                        
                    time.sleep(0.5)
                    print(f"Pasted chunk {i+1}/{len(chunks)}")
                
                # Restore original clipboard content
                pyperclip.copy(original_clipboard)
                return True
            else:
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
        Type content while preserving HTML formatting.
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
                # Not formatted or simple formatting, use regular typing method
                return self.type_content(editor, content)
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
                
                # Set existing text directly using JavaScript
                if len(existing_text) > 0:
                    self.driver.execute_script(f"arguments[0].innerHTML = '{existing_text}';", editor)
                    
                content = remaining_text
            else:
                # Clear existing content if any
                editor.clear()
            
            # Record start time for progress estimation
            self.start_time = time.time()
            
            # Type the content character by character
            total_chars = len(content)
            for i, char in enumerate(content):
                current_pos = start_pos + i
                
                # Escape special characters for JavaScript
                escaped_char = char.replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                
                # Use JavaScript to insert the character (more reliable than send_keys for some editors)
                script = f"arguments[0].innerHTML = arguments[0].innerHTML + '{escaped_char}';"
                self.driver.execute_script(script, editor)
                
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

    def save_session(self):
        """
        Save current session data to file for resuming later.
        Stores URL, file path, progress, and timestamp.
        """
        try:
            session_data = {
                "url": self.args.url,
                "file": self.args.file,
                "progress": self.progress,
                "timestamp": datetime.now().isoformat()
            }
            
            # Write session data as JSON to file
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f)
        except Exception as e:
            print(f"Warning: Failed to save session: {e}")

    def load_session(self):
        """
        Load previous session data if available.
        Prompts user to resume or start over.
        """
        try:
            if os.path.exists(self.session_file):
                # Read session data from file
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Check if session is for the same URL and file
                if session_data["url"] == self.args.url and session_data["file"] == self.args.file:
                    self.progress = session_data["progress"]
                    print(f"Found saved session from {session_data['timestamp']}")
                    print(f"Progress: {self.progress} characters typed")
                    
                    # Handle reset flag or prompt for user choice
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
            
            if editor:
                success = False
                
                # Try clipboard method first if not disabled
                if not self.args.no_clipboard:
                    clipboard_success = self.try_clipboard_paste(editor)
                    if clipboard_success:
                        success = True
                
                # If clipboard failed or was disabled, try character-by-character typing
                if not success:
                    if self.args.formatted:
                        success = self.type_formatted_content(editor, self.content)
                    else:
                        success = self.type_content(editor, self.content)
                
                if success:
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
    """
    Parse command line arguments using argparse.
    Defines all the options available for configuring the script.
    
    Returns:
        Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description='Automate typing text into TinyMCE editor')
    parser.add_argument('url', help='URL of the page with TinyMCE editor')
    parser.add_argument('file', help='Path to the text file containing content to type')
    parser.add_argument('--browser', choices=['chrome', 'firefox'], default='chrome',
                        help='Browser to use (default: chrome)')
    parser.add_argument('--iframe-id', default='', 
                        help='ID of the iframe containing TinyMCE (if applicable)')
    parser.add_argument('--editor-id', default='', 
                        help='ID of the TinyMCE editor element (if known)')
    parser.add_argument('--type-delay', type=float, default=0.01,
                        help='Delay between keystrokes in seconds (default: 0.01)')
    parser.add_argument('--formatted', action='store_true',
                        help='Preserve HTML formatting in the content')
    parser.add_argument('--no-clipboard', action='store_true',
                        help='Disable clipboard paste attempt')
    parser.add_argument('--no-session', action='store_true',
                        help='Disable session saving/loading')
    parser.add_argument('--reset', action='store_true',
                        help='Reset progress from previous session')
    parser.add_argument('--detect-multiple', action='store_true',
                        help='Detect and select from multiple TinyMCE editors')
    return parser.parse_args()


# Main script entry point
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Display welcome message
    print("\n========== TinyMCE Typer ==========")
    print("This script automates typing text into a TinyMCE editor")
    print("Press Ctrl+C in this terminal to exit the script\n")
    
    # Create instance and run the typer
    typer = TinyMCETyper(args)
    typer.run()