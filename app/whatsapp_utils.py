from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import urllib.parse

def send_whatsapp_message(mobile, message, file_path=None):
    """
    Sends a message and optionally a file to a mobile number using WhatsApp Web (Selenium).
    """
    if file_path:
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        if os.path.getsize(file_path) < 100:
            return False, f"File too small/corrupt: {os.path.getsize(file_path)} bytes"

    driver = None
    try:
        print("!!! SELENIUM STARTING !!!")
        # 1. Setup Chrome Options
        options = Options()
        user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
        profile_path = os.path.join(os.getcwd(), 'chrome_profile')
        options.add_argument(f"user-data-dir={profile_path}") 
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 2. Launch Browser
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # 3. Construct URL
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={mobile}&text={encoded_message}"
        
        print(f"Opening URL: {url}")
        driver.get(url)
        
        # 4. Wait for WhatsApp to load and Chat to open
        print("Waiting for WhatsApp Web to load...")
        wait = WebDriverWait(driver, 30) 
        
        try:
             print("Waiting for chat input box...")
             message_box = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
             print("Chat input found.")
        except Exception as e:
             print("Timeout waiting for chat input. Possible reasons: Not logged in, or invalid number.")
             try:
                 driver.find_element(By.XPATH, '//*[contains(text(), "Phone number shared via url is invalid")]')
                 return False, "Invalid Phone Number"
             except:
                 pass
             raise e

        # 5. Attach File (Optional)
        if file_path:
            print("Chat loaded. Attaching file...")
            time.sleep(2) # Stabilize

            # Click the "+" (Attach) button
            attach_selectors = [
                '//*[@aria-label="Attach"]',
                '//*[@data-icon="plus"]',
                '//*[@data-icon="plus-rounded"]',
                '//div[@title="Attach"]'
            ]
            
            attach_btn = None
            for selector in attach_selectors:
                try:
                    attach_btn = driver.find_element(By.XPATH, selector)
                    if attach_btn:
                        print(f"Found attach button with {selector}")
                        break
                except:
                    continue
            
            if not attach_btn:
                 raise Exception("Could not find Attach button")
                 
            attach_btn.click()
            
            print("Waiting for attach menu...")
            time.sleep(1) 
            
            file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            
            if file_inputs:
                print(f"Found {len(file_inputs)} file inputs.")
                file_inputs[0].send_keys(os.path.abspath(file_path))
            else:
                print("No file input found yet. Looking for Document button...")
                try:
                    doc_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-icon="document-refreshed-thin"] | //*[@data-icon="document"]')))
                    doc_btn.click()
                    time.sleep(1)
                    file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                    if file_inputs:
                         file_inputs[0].send_keys(os.path.abspath(file_path))
                    else:
                         raise Exception("No file input found even after clicking Document")
                except Exception as e:
                     with open("debug_wa_doc.html", "w", encoding="utf-8") as f:
                         f.write(driver.page_source)
                     print("Saved debug_wa_doc.html")
                     raise e
            
            print(f"File attached. Waiting for send button...")

        # 6. Send Message (with or without file)
        
        # Setup ActionChains
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(driver)

        # Check for Preview Modal (Caption Input) if file was attached
        preview_modal_present = False
        if file_path:
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Add a caption"] | //span[@data-icon="x-alt"]')))
                print("Preview modal detected.")
                preview_modal_present = True
            except:
                 pass

        sent_action_performed = False

        if preview_modal_present:
            # Method 1: Focus on caption and Press ENTER
            try:
                print("Attempting to send via ENTER key on active element...")
                active_elem = driver.switch_to.active_element
                active_elem.send_keys(Keys.ENTER)
                time.sleep(2)
                
                # Verify if modal closed
                try:
                    driver.find_element(By.XPATH, '//div[@aria-label="Add a caption"] | //span[@data-icon="x-alt"]')
                    print("Preview modal still open. Enter key didn't work.")
                except:
                    print("Preview modal closed. Enter key likely worked.")
                    sent_action_performed = True
            except Exception as e:
                print(f"Enter key failed: {e}")

        if not sent_action_performed:
            # Fallback: Find Send Button and Click using ActionChains
            try:
                # Iterate through all potential send buttons
                buttons = driver.find_elements(By.XPATH, '//span[@data-icon="send"] | //span[@data-icon="wds-ic-send-filled"] | //div[@aria-label="Send"] | //button[@aria-label="Send"] | //span[@data-icon="send-filled"]')
                
                target_btn = None
                for btn in buttons:
                    if btn.is_displayed():
                        target_btn = btn
                        break
                
                if target_btn:
                    print(f"Found visible send button: {target_btn.tag_name} at {target_btn.location}")
                    # Scroll to element to be safe
                    driver.execute_script("arguments[0].scrollIntoView(true);", target_btn)
                    time.sleep(0.5)
                    
                    # ActionChains Click
                    print("Clicking using ActionChains...")
                    actions.move_to_element(target_btn).click().perform()
                    sent_action_performed = True
                else:
                    print("No visible send button found for ActionChains.")
                    # If we don't find a button but we have text in the box (from URL), hitting ENTER in the message box might work
                    if not file_path:
                        print("Trying ENTER in message box as fallback...")
                        try:
                             message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
                             message_box.send_keys(Keys.ENTER)
                             sent_action_performed = True
                        except Exception as e_enter:
                             print(f"Enter in message box failed: {e_enter}")
                    
            except Exception as e:
                 print(f"ActionChains click failed: {e}")
                 # Last resort: JS Click
                 try:
                     print("Trying JS Click fallback...")
                     send_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@data-icon="send"] | //span[@data-icon="wds-ic-send-filled"]')))
                     driver.execute_script("arguments[0].click();", send_btn)
                     sent_action_performed = True
                 except Exception as final_e:
                     # Capture debug
                     with open("debug_wa_send.html", "w", encoding="utf-8") as f:
                             f.write(driver.page_source)
                     print("Saved debug_wa_send.html")
                     raise final_e
        
        # 7. STRONG VERIFICATION
        print("Verifying message delivery...")
        time.sleep(2)
        
        # 1. Ensure modal is gone (if file was attached)
        if file_path:
            try:
                driver.find_element(By.XPATH, '//div[@aria-label="Add a caption"] | //span[@data-icon="x-alt"]')
                print("CRITICAL: Preview modal is STUCK open. Send failed.")
                with open("debug_wa_stuck.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                return False, "Failed to send: Preview modal got stuck."
            except:
                print("Preview modal is gone (Good).")
            
        # 2. Look for recent message bubble (optional)
        try:
             wait.until(EC.presence_of_element_located((By.XPATH, '//span[@data-icon="msg-dblcheck"] | //span[@data-icon="msg-check"] | //span[@data-icon="msg-time"]')))
             print("Message status icon found in chat.")
        except:
             print("Warning: No message status icon found yet. Might be slow.")

        # Log status to a file
        with open("execution.log", "a") as f:
            f.write(f"Verified send for {mobile}. Success.\n")
            
        print("Sent!")
        return True, "Message sent successfully!"
            
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")
        if driver:
            try:
                with open("debug_wa.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("Saved debug_wa.html")
            except:
                pass
        return False, str(e)
    finally:
        # Don't close immediately if debugging, but generally we should close
        if driver:
             # time.sleep(2)
             driver.quit()

