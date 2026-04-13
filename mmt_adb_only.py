import subprocess
import time
import os

# CONFIGURATION
ADB_PATH = r"C:\Users\mohds\AppData\Local\Android\Sdk\platform-tools\adb.exe"

def adb_call(command_list):
    full_cmd = [ADB_PATH] + command_list
    return subprocess.run(full_cmd, capture_output=True, text=True)

def adb_tap(x, y, label=""):
    print(f"[TAP] {label} at ({x}, {y})")
    adb_call(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(3)

def adb_type(text, label=""):
    print(f"[TYPE] {label}: {text}")
    # Small delay to ensure focus
    time.sleep(1)
    adb_call(['shell', 'input', 'text', text])
    time.sleep(2)

def launch_mmt():
    print("[ACTION] Launching MakeMyTrip...")
    adb_call(['shell', 'am', 'force-stop', 'com.makemytrip'])
    time.sleep(1)
    adb_call(['shell', 'am', 'start', '-n', 'com.makemytrip/com.mmt.travel.app.home.ui.SplashActivityPrimary'])
    print("[WAIT] Waiting for app to load (15s)...")
    time.sleep(15)

def run_sequence():
    launch_mmt()

    # 1. Select Flights Tab (Home Screen)
    # Flights is usually the first big icon. 
    adb_tap(120, 380, "Flights Tab")

    # 2. Click From Box (Search Screen)
    # Tapping the 'FROM' area
    adb_tap(280, 250, "From Select Box") 
    time.sleep(2)
    
    # 3. Enter Hyderabad
    # If the search window opens, this types into the search field
    adb_type("Hyderabad", "From City")
    time.sleep(4) # More time for suggestions to load
    
    # 4. Select Suggestion (HYD)
    # Suggestion 1 in the search list is usually around X=500, Y=400
    adb_tap(500, 400, "Select Hyderabad (HYD) Suggestion")
    time.sleep(3)

    # 5. Click To Box
    # Now that we are back on the search screen, click the 'TO' box
    adb_tap(650, 250, "To Select Box")
    time.sleep(2)

    # 6. Enter Delhi
    adb_type("Delhi", "To City")
    time.sleep(4) # More time for suggestions
    
    # 7. Select Suggestion (DEL) 
    # Target Suggestion 1 in the search list
    adb_tap(500, 400, "Select Delhi (DEL) Suggestion")
    time.sleep(3)

    # 8. Trigger Search Flights
    # Search is the blue button in the center-ish vertically
    adb_tap(450, 545, "Click Blue SEARCH FLIGHTS Button")
    time.sleep(10)

    # 9. Select Flight Result (Avoiding Top Ad)
    print("[WAIT] Loading Results (12s)...")
    time.sleep(12)
    # Tapping lower down to skip 'Sponsored' flights
    adb_tap(540, 1100, "Click First Non-Ad Flight Card")

    print("[DONE] Sequence Complete.")

if __name__ == "__main__":
    run_sequence()
