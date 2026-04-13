from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import time
import os

# CONFIGURATION
DEVICE_NAME = "a6ecddd5"
ADB_PATH = r"C:\Users\mohds\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def type_adb(text):
    print(f"  [ADB] Typing: {text}")
    subprocess.run([ADB_PATH, 'shell', 'input', 'text', text])
    time.sleep(2)

def tap_coord(x, y, label=""):
    print(f"  [TAP] {label} at ({x}, {y})")
    subprocess.run([ADB_PATH, 'shell', 'input', 'tap', str(x), str(y)])
    time.sleep(3)

options = UiAutomator2Options()
options.platform_name = "Android"
options.device_name = DEVICE_NAME
options.app_package = "com.makemytrip"
options.app_activity = "com.mmt.travel.app.home.ui.SplashActivityPrimary"
options.no_reset = True
# Force start the app explicitly using ADB and wait
def launch_mmt():
    print("[ADB] Force launching MakeMyTrip...")
    # Using the detected ADB path
    subprocess.run([ADB_PATH, 'shell', 'am', 'force-stop', 'com.makemytrip'])
    time.sleep(1)
    subprocess.run([ADB_PATH, 'shell', 'am', 'start', '-n', 'com.makemytrip/com.mmt.travel.app.home.ui.SplashActivityPrimary'])
    time.sleep(15) 

launch_mmt()

print("Connecting to Appium...")
# On Android 14, ignoreHiddenApiPolicyError causes permission issues. 
# We remove it since we already force-launched the app.
options.set_capability("appium:skipDeviceInitialization", True)
driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

print("Waiting for app/popups...")
time.sleep(10)

# 1. Open Flights Tab (ensure we aren't in Hotels/Ads)
print("Step 0: Ensure Flights Tab")
# Flights is usually the first icon on the left.
# Hotels is to its right. We'll try to find "Flights" by text first.
try:
    driver.find_element(AppiumBy.XPATH, '//android.widget.TextView[@text="Flights"]').click()
except:
    tap_coord(150, 450, "Flights Icon (Fallback)")
time.sleep(3)

# 1. Open From City - Based on image, it's roughly x=300, y=700 (MMT Flight Search screen)
print("Step 1: Open From City")
# We'll use a more accurate coordinate from typical 1080p layout context
tap_coord(300, 650, "From Box")

# 2. Type Hyderabad
print("Step 2: Type Hyderabad")
type_adb("Hyderabad")

# 3. Select first suggestion
print("Step 3: Select Suggestion")
tap_coord(500, 500, "First Suggestion")

# 4. Open To City - Approx center-right of From box
print("Step 4: Open To City")
tap_coord(750, 650, "To Box")

# 5. Type Delhi
print("Step 5: Type Delhi")
type_adb("Delhi")

# 6. Select first suggestion
print("Step 6: Select Suggestion")
tap_coord(500, 500, "First Suggestion")

# 7. Search Flights - Search button "SEARCH FLIGHTS" is a large blue button below the search block.
print("Step 7: Search Flights")
tap_coord(540, 1500, "Search Button") 

# 8. Handle Departure Date if open
print("Step 8: Handle Departure Date")
# Often MMT opens a calendar automatically.
tap_coord(500, 1500, "Select Central Date (Approx)")
time.sleep(2)
tap_coord(540, 2200, "Done/Search Final")

# 9. Final Search Trigger (if needed)
print("Step 9: Final Search Trigger")
tap_coord(540, 1150, "Final Search Button")

# 10. Select First Flight Result
print("Step 10: Select First Flight")
time.sleep(10)
tap_coord(540, 600, "First Flight Result")

print("Sequence Complete.")
driver.quit()
