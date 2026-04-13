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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("GOIBIBO")

step_count = 0
interruptions = []


def step(label: str):
    global step_count
    step_count += 1
    log.info(f"[STEP {step_count}] {label}")


def note_interruption(desc: str):
    interruptions.append(desc)
    log.warning(f"[INTERRUPTION] {desc}")

def wait_and_click(driver, wait, locator, label="element", timeout=15):
    elem = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    try:
        elem.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", elem)
    step(f"Clicked: {label}")
    return elem


def dismiss_popup(driver):
    """
    Goibibo shows various overlays (app download prompts, login nudges, etc.)
    Try common close patterns. Not counted as a step.
    """
    selectors = [
        (By.CSS_SELECTOR, "span.commonModal__close"),
        (By.CSS_SELECTOR, "div[class*='closeBtn']"),
        (By.CSS_SELECTOR, "button[class*='close']"),
        (By.XPATH, "//button[@aria-label='Close' or @aria-label='close']"),
        (By.XPATH, "//span[contains(@class,'close') and not(ancestor::*[contains(@style,'display:none')])]"),
    ]
    for locator in selectors:
        try:
            btn = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(locator))
            btn.click()
            note_interruption("Dismissed modal/popup overlay")
            time.sleep(0.4)
            return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False


def type_in_field(driver, wait, locator, text, label):
    """Click a field, clear it, and type text."""
    field = wait.until(EC.element_to_be_clickable(locator))
    field.click()
    step(f"Clicked field: {label}")
    field.clear()
    field.send_keys(text)
    time.sleep(1)

def run():
    global step_count, interruptions
    step_count = 0
    interruptions = []

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.goibibo.com/")
        homepage_ready = time.time()
        log.info("Homepage loaded. Timer started.")
        time.sleep(2)
        dismiss_popup(driver)

        try:
            flights_nav = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//a[contains(@href,'flights') and contains(normalize-space(.),'Flights')]"
                     " | //li[contains(@class,'flights') or contains(normalize-space(.),'Flights')]")
                )
            )
            flights_nav.click()
            step("Clicked Flights in navigation")
            time.sleep(1.5)
        except TimeoutException:
            step("Flights section already active")


        try:
            one_way = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//label[contains(.,'One Way') or contains(.,'ONE WAY')]"
                     " | //span[contains(text(),'One Way')]"
                     " | //input[@value='ONE_WAY']/following-sibling::label")
                )
            )
            one_way.click()
            step("Selected One Way")
        except TimeoutException:
            note_interruption("Could not find explicit One-Way option; may be default")

        from_locator = (
            By.XPATH,
            "//input[@placeholder='From' or @id='gosuggest_input_from' or contains(@class,'fromCity')]"
            " | //div[contains(@class,'fromCity')]//input"
        )
        type_in_field(driver, wait, from_locator, "Hyderabad", "From city")

        
        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//ul[contains(@class,'ui-autocomplete')]//li[contains(.,'Hyderabad') and contains(.,'HYD')]"
             " | //div[contains(@class,'suggest') and contains(.,'Hyderabad') and contains(.,'HYD')]"
             " | //li[contains(@class,'airportSuggest') and contains(.,'HYD')]"),
            "Hyderabad (HYD) suggestion",
        )

        
        to_locator = (
            By.XPATH,
            "//input[@placeholder='To' or @id='gosuggest_input_to' or contains(@class,'toCity')]"
            " | //div[contains(@class,'toCity')]//input"
        )
        
        try:
            to_field = WebDriverWait(driver, 4).until(EC.element_to_be_clickable(to_locator))
        except TimeoutException:
            to_field = driver.find_element(*to_locator)

        to_field.clear()
        to_field.click()
        step("Clicked To field")
        to_field.send_keys("Delhi")
        time.sleep(1)

        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//ul[contains(@class,'ui-autocomplete')]//li[contains(.,'Delhi') and (contains(.,'DEL') or contains(.,'Indira'))]"
             " | //div[contains(@class,'suggest') and contains(.,'Delhi') and contains(.,'DEL')]"
             " | //li[contains(@class,'airportSuggest') and contains(.,'DEL')]"),
            "Delhi (DEL) suggestion",
        )

        
        date_locator = (
            By.XPATH,
            "//input[@placeholder='Departure' or contains(@class,'depart') or @id='departure_date']"
            " | //div[contains(@class,'dept-date') or contains(@class,'departureDate')]"
        )
        wait_and_click(driver, wait, date_locator, "Departure date field")

        
        for _ in range(15):
            try:
                caption = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'DayPicker-Caption') or contains(@class,'month-title') "
                    "or contains(@class,'calendarMonth')]"
                ).text
                if "June 2026" in caption or "Jun 2026" in caption:
                    break
                next_month_btn = driver.find_element(
                    By.XPATH,
                    "//span[@aria-label='Next Month' or @aria-label='next month']"
                    " | //button[contains(@class,'DayPicker-NavButton--next') or contains(@class,'next-month')]"
                    " | //div[contains(@class,'nextMonth')]"
                )
                next_month_btn.click()
                step("Calendar → next month")
                time.sleep(0.4)
            except NoSuchElementException:
                break

        
        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//div[@aria-label='Mon Jun 15 2026' or @aria-label='June 15, 2026']"
             " | //td[@aria-label='June 15, 2026']"
             " | //div[contains(@class,'DayPicker-Day') and not(contains(@class,'outside'))"
             "         and not(contains(@class,'disabled')) and normalize-space(text())='15']"),
            "June 15 on calendar",
        )
        time.sleep(1)

        
        try:
            done_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Done') or contains(text(),'Apply')]")
                )
            )
            done_btn.click()
            step("Confirmed traveller count (Done)")
        except TimeoutException:
            pass  

        
        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//button[contains(text(),'Search') or contains(text(),'SEARCH')]"
             " | //a[contains(@class,'search-btn') and (contains(.,'Search') or contains(.,'SEARCH'))]"),
            "Search button",
        )
        time.sleep(3)
        dismiss_popup(driver)
        log.info("Search results page loaded.")

        
        try:
            price_sort = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//li[contains(@class,'sort') and (contains(.,'Price') or contains(.,'Cheapest'))]"
                     " | //div[contains(@class,'sortOption') and (contains(.,'Price') or contains(.,'Cheapest'))]"
                     " | //span[text()='Price' or text()='Cheapest' or text()='Lowest Price']")
                )
            )
            price_sort.click()
            step("Sorted by Price / Cheapest")
            time.sleep(2)
        except TimeoutException:
            note_interruption("Sort by Price button not found – results may already be sorted by price by default")

        
        first_result = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "(//div[contains(@class,'flightCard') or contains(@class,'FlightCard') "
                 "or contains(@class,'resultItem') or contains(@class,'flight-item')])[1]")
            )
        )
        first_result.click()
        step("Clicked first flight card")
        time.sleep(2)
        dismiss_popup(driver)

        
        try:
            book_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//button[contains(text(),'Book Now') or contains(text(),'BOOK NOW') "
                     "or contains(text(),'Select') or contains(text(),'SELECT')]")
                )
            )
            book_btn.click()
            step("Clicked Book Now / Select")
            time.sleep(2)
        except TimeoutException:
            note_interruption("No Book Now button found after expanding flight card")

        
        dismiss_popup(driver)

        
        for attempt in range(5):
            current_url = driver.current_url
            if "payment" in current_url.lower() or "pay" in current_url.lower():
                log.info("Reached payment page – stopping as required.")
                break
            try:
                cont = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//button[contains(text(),'Continue') or contains(text(),'CONTINUE') "
                         "or contains(text(),'Proceed') or contains(text(),'Next')]")
                    )
                )
                cont.click()
                step(f"Clicked Continue/Proceed (step {attempt + 1})")
                time.sleep(2)
                dismiss_popup(driver)
            except TimeoutException:
                log.info("No more Continue buttons – likely on review or payment page.")
                break

        
        end_time = time.time()
        total_seconds = round(end_time - homepage_ready, 2)

        
        log.info("=" * 60)
        log.info("GOIBIBO AUTOMATION COMPLETE")
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