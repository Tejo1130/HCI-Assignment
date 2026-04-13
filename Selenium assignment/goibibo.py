import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

opts = Options()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-notifications")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=opts)

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
    time.sleep(1)

def dismiss_popups():
    """Close any visible modal/overlay."""
    close_xpaths = [
        "//*[contains(@class,'close') and (self::button or self::span or self::div)]",
        "//*[@aria-label='Close'] | //*[@aria-label='close']",
        "//button[text()='×'] | //span[text()='×']",
        "//button[contains(text(),'Skip')] | //button[contains(text(),'Later')]",
    ]
    for xp in close_xpaths:
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                if el.is_displayed():
                    driver.execute_script("arguments[0].click();", el)
                    global steps
                    steps += 1
                    print(f"  Step {steps:2d} |    --- | Closed pop-up")
                    time.sleep(1)
                    return True
        except:
            pass
    return False

print("\n── Goibibo Web Automation ──")
driver.get("https://www.goibibo.com/")
start_time = time.time()
time.sleep(3)

dismiss_popups()

try:
    click("//a[contains(text(),'Flights')] | //span[text()='Flights']", "Click Flights tab")
except TimeoutException:
    print("  (Already on Flights)")

try:
    click(
        "//li[@value='ONE'] | //label[contains(.,'One Way')] | //span[contains(text(),'One Way')]",
        "Click One Way"
    )
except TimeoutException:
    print("  (One Way already selected)")

dismiss_popups()
from_field = wait.until(EC.element_to_be_clickable((By.XPATH,
    "//input[@id='gosuggest_input_src'] | //input[@placeholder='From']"
)))
from_field.clear()
from_field.send_keys("Hyderabad")
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Type 'Hyderabad' in From")
time.sleep(1.5)

click("//li[contains(.,'Hyderabad')] | //li[contains(.,'HYD')]", "Select Hyderabad (HYD)")

to_field = wait.until(EC.element_to_be_clickable((By.XPATH,
    "//input[@id='gosuggest_input_dst'] | //input[@placeholder='To']"
)))
to_field.clear()
to_field.send_keys("Delhi")
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Type 'Delhi' in To")
time.sleep(1.5)

click("//li[contains(.,'Delhi')] | //li[contains(.,'DEL')]", "Select Delhi (DEL)")

click(
    "//input[@id='depart_date'] | //div[contains(@class,'dept_date')]",
    "Open departure date picker"
)

for _ in range(8):
    try:
        driver.find_element(By.XPATH, "//*[contains(text(),'June') and contains(text(),'2026')]")
        break
    except NoSuchElementException:
        click(
            "//span[contains(@class,'next')] | //i[contains(@class,'icon-right')]",
            "Next month"
        )

click(
    "//td[@data-date='2026-06-15'] | //div[@aria-label='June 15, 2026']",
    "Select 15 June 2026"
)

dismiss_popups()
click(
    "//button[contains(@class,'search')] | //button[contains(text(),'Search')]",
    "Click Search"
)

print("\n  Waiting for results...")
try:
    wait.until(EC.presence_of_element_located((By.XPATH,
        "//div[contains(@class,'flightCard')] | //div[contains(@class,'resultItem')]"
    )))
    steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Results loaded")
except TimeoutException:
    print("  WARNING: Results page slow to load")

time.sleep(2)
dismiss_popups()

click(
    "//span[contains(text(),'Price')] | //button[contains(text(),'Cheapest')] | //label[contains(.,'Price')]",
    "Sort by Price"
)
time.sleep(2)

cards = wait.until(EC.presence_of_all_elements_located((By.XPATH,
    "//div[contains(@class,'flightCard')] | //li[contains(@class,'resultItem')]"
)))
first_flight = cards[0]
try:
    fare = first_flight.find_element(By.XPATH, ".//*[contains(@class,'price')]").text
except:
    fare = "N/A"

driver.execute_script("arguments[0].click();", first_flight)
steps += 1; print(f"  Step {steps:2d} | {round(time.time()-start_time,1):6.1f}s | Select cheapest flight (fare: {fare})")
time.sleep(2)

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
        time.sleep(2)
    except TimeoutException:
        break

total_time = round(time.time() - start_time, 1)
print(f"\n{'─'*45}")
print(f"  Platform  : Goibibo (Web)")
print(f"  Steps     : {steps}")
print(f"  Time      : {total_time}s ({round(total_time/60,1)} min)")
print(f"  Cheapest  : {fare}")
print(f"{'─'*45}\n")

input("Press Enter to close browser...")
driver.quit()