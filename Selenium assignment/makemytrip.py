import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ── Setup ─────────────────────────────────────────────────────────────────────
opts = Options()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-notifications")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=opts)
# Hide webdriver property from JS detection
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})
wait = WebDriverWait(driver, 10)

steps = 0
start_time = None

def click(xpath, label):
    global steps
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    try:
        el.click()
    except:
        driver.execute_script("arguments[0].click();", el)
    steps += 1
    elapsed = round(time.time() - start_time, 1) if start_time else 0
    print(f"  Step {steps:2d} | {elapsed:6.1f}s | {label}")

def dismiss_popups():
    """Close any visible modal/overlay."""
    close_xpaths = [
        "//span[@data-cy='closeModal']",
        "//*[contains(@class,'modal')]//span[text()='×']",
        "//button[contains(@class,'close')]",
        "//div[contains(@class,'modalContent')]//span[contains(@class,'close')]",
        "//*[@aria-label='Close']",
    ]
    for xp in close_xpaths:
        try:
            btn = driver.find_element(By.XPATH, xp)
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                global steps
                steps += 1
                print(f"  Step {steps:2d} |    --- | Closed pop-up")
                return True
        except NoSuchElementException:
            pass
    return False

print("\n── MakeMyTrip Web Automation ──")
driver.get("https://www.makemytrip.com/")
start_time = time.time()

dismiss_popups()

try:
    click("//li[@data-cy='oneWay']", "Click One Way")
except TimeoutException:
    print("  (One Way already selected)")

dismiss_popups()
from_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='fromCity']")))
from_field.clear()
from_field.send_keys("Hyderabad")
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Type 'Hyderabad' in From")

click("//li[contains(.,'Hyderabad') and contains(.,'HYD')]", "Select Hyderabad (HYD)")

to_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='toCity']")))
to_field.clear()
to_field.send_keys("Delhi")
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Type 'Delhi' in To")

click("//li[contains(.,'Delhi') and contains(.,'DEL')]", "Select Delhi (DEL)")

click("//div[@id='departure']", "Open departure date picker")

for _ in range(8):
    try:
        driver.find_element(By.XPATH, "//*[contains(text(),'June') and contains(text(),'2026')]")
        break
    except NoSuchElementException:
        click("//span[contains(@class,'next')] | //button[contains(@aria-label,'Next')]", "Next month")

click(
    "//div[@aria-label='Mon Jun 15 2026'] | //p[@aria-label='Mon Jun 15 2026']",
    "Select 15 June 2026"
)

dismiss_popups()
click(
    "//a[contains(@class,'search_btn')] | //button[contains(text(),'Search')]",
    "Click Search"
)

print("\n  Waiting for results...")
try:
    wait.until(EC.presence_of_element_located((By.XPATH,
        "//div[contains(@class,'listingCard')] | //div[contains(@class,'flightItem')]"
    )))
    steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Results loaded")
except TimeoutException:
    print("  WARNING: Results page slow to load")

dismiss_popups()

click(
    "//span[contains(text(),'Price')] | //div[contains(@class,'sort')]//span[contains(.,'Price')]",
    "Sort by Price"
)

first_flight = wait.until(EC.element_to_be_clickable((By.XPATH,
    "(//div[contains(@class,'listingCard')])[1] | (//div[contains(@class,'flightItem')])[1]"
)))
try:
    fare = first_flight.find_element(By.XPATH, ".//*[contains(@class,'price')]").text
except:
    fare = "N/A"

driver.execute_script("arguments[0].click();", first_flight)
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Select cheapest flight (fare: {fare})")

for label in ["Book Now", "Continue", "Continue"]:
    try:
        btn = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH,
            f"//button[contains(text(),'{label}')] | //a[contains(text(),'{label}')]"
        )))
        if any(kw in driver.current_url.lower() for kw in ["payment", "pay"]):
            print(f"  ✓ Reached payment boundary — stopping")
            break
        driver.execute_script("arguments[0].click();", btn)
        steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Click '{label}'")
    except TimeoutException:
        break

total_time = round(time.time() - start_time, 1)
print(f"\n{'─'*45}")
print(f"  Platform  : MakeMyTrip (Web)")
print(f"  Steps     : {steps}")
print(f"  Time      : {total_time}s ({round(total_time/60,1)} min)")
print(f"  Cheapest  : {fare}")
print(f"{'─'*45}\n")

input("Press Enter to close browser...")
driver.quit()