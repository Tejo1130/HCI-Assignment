"""
MakeMyTrip - Selenium Flight Booking Automation
BITS F364 HCI - Programming Assignment (Part A)

Task:
  - From: Hyderabad (HYD)
  - To: Delhi (DEL)
  - Date: 15 June 2026
  - Passengers: 1 Adult, Economy
  - Sort by price (lowest), select first result, stop before payment

Measurement:
  - Steps counted as discrete user interactions (click, type, select)
  - Time measured from homepage ready → review/itinerary page loaded
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("MMT")

# ── Measurement counters ──────────────────────────────────────────────────────
step_count = 0
interruptions = []


def step(label: str):
    """Increment step counter and log."""
    global step_count
    step_count += 1
    log.info(f"[STEP {step_count}] {label}")


def note_interruption(desc: str):
    interruptions.append(desc)
    log.warning(f"[INTERRUPTION] {desc}")


# ── Helper utilities ──────────────────────────────────────────────────────────
def wait_and_click(driver, wait, locator, label="element", timeout=15):
    """Wait for an element, scroll into view, and click it."""
    elem = wait.until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    try:
        elem.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", elem)
    step(f"Clicked: {label}")
    return elem


def dismiss_popup(driver, wait):
    """
    Attempt to close any modal / login overlay that MakeMyTrip commonly shows.
    Not counted as a task step but recorded as an interruption.
    """
    popup_selectors = [
        (By.CSS_SELECTOR, "span.commonModal__close"),
        (By.CSS_SELECTOR, "div.loginModal__close"),
        (By.XPATH, "//span[contains(@class,'close') and not(ancestor::*[contains(@style,'display:none')])]"),
        (By.CSS_SELECTOR, "button.cross__btn"),
    ]
    for locator in popup_selectors:
        try:
            btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(locator))
            btn.click()
            note_interruption("Dismissed modal/popup overlay")
            time.sleep(0.5)
            return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False


# ── Main automation ───────────────────────────────────────────────────────────
def run():
    global step_count, interruptions
    step_count = 0
    interruptions = []

    # Chrome options – run headed so pop-ups behave naturally
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # Uncomment the next line to run headless (pop-up handling may differ):
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # ── 1. Open homepage ──────────────────────────────────────────────────
        driver.get("https://www.makemytrip.com/")
        # Start timer AFTER page is ready
        homepage_ready = time.time()
        log.info("Homepage loaded. Timer started.")
        time.sleep(2)  # allow JS to settle

        # Dismiss any immediate login modal
        dismiss_popup(driver, wait)

        # ── 2. Ensure "Flights" tab is active ────────────────────────────────
        try:
            flights_tab = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//li[contains(@class,'menu_Flights') or .//span[text()='Flights']]")
                )
            )
            flights_tab.click()
            step("Clicked Flights tab")
        except TimeoutException:
            step("Flights tab already active (no click needed)")

        # ── 3. Select One-Way ────────────────────────────────────────────────
        wait_and_click(
            driver, wait,
            (By.XPATH, "//label[@for='trip_type_ONE_WAY' or contains(.,'One Way')]"),
            "One Way radio button",
        )

        # ── 4. Set Departure city ────────────────────────────────────────────
        from_field = wait.until(
            EC.element_to_be_clickable((By.ID, "fromCity"))
        )
        from_field.click()
        step("Clicked From field")
        from_field.clear()
        from_field.send_keys("Hyderabad")
        time.sleep(1)
        wait_and_click(
            driver, wait,
            (By.XPATH, "//li[contains(@class,'react-autosuggest') and contains(.,'HYD') and contains(.,'Hyderabad')]"),
            "Hyderabad suggestion",
        )

        # ── 5. Set Destination city ──────────────────────────────────────────
        to_field = wait.until(
            EC.element_to_be_clickable((By.ID, "toCity"))
        )
        to_field.click()
        step("Clicked To field")
        to_field.clear()
        to_field.send_keys("Delhi")
        time.sleep(1)
        wait_and_click(
            driver, wait,
            (By.XPATH, "//li[contains(@class,'react-autosuggest') and (contains(.,'DEL') or contains(.,'Indira Gandhi'))]"),
            "Delhi suggestion",
        )

        # ── 6. Set departure date (15 June 2026) ─────────────────────────────
        date_field = wait.until(
            EC.element_to_be_clickable((By.ID, "departure"))
        )
        date_field.click()
        step("Clicked departure date field")

        # Navigate calendar to June 2026
        # Current displayed month may vary; keep clicking Next until June 2026
        for _ in range(15):  # safety cap
            try:
                month_year = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'DayPicker-Caption') or contains(@class,'month_year_title')]"
                ).text
                if "June 2026" in month_year or "Jun 2026" in month_year:
                    break
                next_btn = driver.find_element(
                    By.XPATH,
                    "//span[contains(@aria-label,'Next Month') or contains(@class,'next_month') or contains(@class,'DayPicker-NavButton--next')]"
                )
                next_btn.click()
                step("Navigated calendar to next month")
                time.sleep(0.4)
            except NoSuchElementException:
                break

        # Click day 15
        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//div[@aria-label='Mon Jun 15 2026' or "
             "@aria-label='June 15, 2026' or "
             "(contains(@class,'DayPicker-Day') and normalize-space(text())='15' and not(contains(@class,'outside')))]"),
            "June 15 on calendar",
        )

        # ── 7. Passengers – 1 adult is default; confirm if picker appears ────
        try:
            pax_done = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Done') or contains(text(),'Apply')]")
                )
            )
            pax_done.click()
            step("Confirmed passenger count (Done)")
        except TimeoutException:
            pass  # Default 1 adult, no action required

        # ── 8. Search ────────────────────────────────────────────────────────
        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//a[contains(@class,'primaryBtn') and (contains(text(),'Search') or contains(text(),'SEARCH'))]"
             " | //button[contains(text(),'Search') or contains(text(),'SEARCH')]"),
            "Search button",
        )

        # Wait for results page
        wait.until(EC.url_contains("flight/search"))
        time.sleep(3)
        dismiss_popup(driver, wait)
        log.info("Search results page loaded.")

        # ── 9. Sort by Price (Cheapest) ──────────────────────────────────────
        try:
            sort_price = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//li[contains(@class,'sort') and (contains(.,'Price') or contains(.,'Cheapest'))]"
                     " | //span[text()='Price' or text()='Cheapest']"
                     " | //div[contains(@data-cy,'sort-price')]")
                )
            )
            sort_price.click()
            step("Sorted by Price (Cheapest)")
            time.sleep(2)
        except TimeoutException:
            note_interruption("Could not find explicit 'Sort by Price' button – may already be default")

        # ── 10. Select first flight ──────────────────────────────────────────
        first_flight = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "(//div[contains(@class,'listingCard') or contains(@class,'FlightCard') or "
                 "contains(@class,'fliCode')])[1]")
            )
        )
        first_flight.click()
        step("Selected first flight from sorted results")
        time.sleep(2)
        dismiss_popup(driver, wait)

        # ── 11. Book / Select button within expanded card ────────────────────
        try:
            book_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[contains(text(),'BOOK NOW') or contains(text(),'Book Now') "
                     "or contains(text(),'SELECT')]")
                )
            )
            book_btn.click()
            step("Clicked BOOK NOW / SELECT")
            time.sleep(2)
        except TimeoutException:
            note_interruption("No explicit Book Now button found after expanding card")

        # ── 12. Handle any login prompts ─────────────────────────────────────
        dismiss_popup(driver, wait)

        # ── 13. Continue through itinerary / traveller pages until payment ───
        for attempt in range(5):
            current_url = driver.current_url
            if "payment" in current_url.lower() or "pay" in current_url.lower():
                break
            try:
                continue_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//button[contains(text(),'Continue') or contains(text(),'CONTINUE') "
                         "or contains(text(),'Proceed') or contains(text(),'Next')]")
                    )
                )
                continue_btn.click()
                step(f"Clicked Continue/Proceed (step {attempt + 1})")
                time.sleep(2)
                dismiss_popup(driver, wait)
            except TimeoutException:
                log.info("No more Continue buttons found – likely on review or payment page.")
                break

        # ── Stop timer ───────────────────────────────────────────────────────
        end_time = time.time()
        total_seconds = round(end_time - homepage_ready, 2)

        # ── Report ────────────────────────────────────────────────────────────
        log.info("=" * 60)
        log.info("MAKEMYTRIP AUTOMATION COMPLETE")
        log.info(f"  Final URL     : {driver.current_url}")
        log.info(f"  Total Steps   : {step_count}")
        log.info(f"  Total Time    : {total_seconds}s ({total_seconds/60:.1f} min)")
        log.info(f"  Interruptions : {len(interruptions)}")
        for i, msg in enumerate(interruptions, 1):
            log.info(f"    {i}. {msg}")
        log.info("=" * 60)

        input("\n[PAUSED] Inspect the browser, then press Enter to close...")

    except Exception as e:
        log.error(f"Automation error: {e}", exc_info=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    run()