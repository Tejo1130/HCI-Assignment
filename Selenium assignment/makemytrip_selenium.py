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
log = logging.getLogger("MMT")


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



def run():
    global step_count, interruptions
    step_count = 0
    interruptions = []

    
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
       
        driver.get("https://www.makemytrip.com/")
        # Start timer AFTER page is ready
        homepage_ready = time.time()
        log.info("Homepage loaded. Timer started.")
        time.sleep(2)  


        dismiss_popup(driver, WebDriverWait(driver, 5))

        
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

       
        try:
            one_way = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//li[@data-cy='oneWay'] | //input[@id='trip_type_ONE_WAY']")
                )
            )
            try:
                one_way.click()
                step("Clicked One Way")
            except:
                driver.execute_script("arguments[0].click();", one_way)
                step("Clicked One Way (JS)")
        except TimeoutException:
            step("One Way already selected / not required")

        
        from_field = wait.until(EC.element_to_be_clickable((By.ID, "fromCity")))
        from_field.click()
        step("Clicked From field")

        time.sleep(2) 

        from_input = wait.until( EC.presence_of_element_located((By.XPATH, "//input[@placeholder='From'] | //input[@type='text']")))

        from_input.send_keys("Hyderabad")
        step("Typed Hyderabad")

    
        wait_and_click(
            driver, wait,
            (By.XPATH, "//li[contains(.,'Hyderabad') and contains(.,'HYD')]"),
            "Hyderabad suggestion",
        )

       
        to_field = wait.until(
            EC.element_to_be_clickable((By.ID, "toCity"))
        )
        to_field.click()
        step("Clicked To field")

        time.sleep(2)

        to_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='To'] | //input[@type='text']"))
        )

        to_input.send_keys("Delhi")
        step("Typed Delhi")

        wait_and_click(
            driver, wait,
            (By.XPATH, "//li[contains(.,'Delhi') and contains(.,'DEL')]"),
            "Delhi suggestion",
        )

        
        date_field = wait.until(
            EC.element_to_be_clickable((By.ID, "departure"))
        )
        date_field.click()
        step("Clicked departure date field")

        
        for _ in range(15):  
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

        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//div[@aria-label='Mon Jun 15 2026' or "
             "@aria-label='June 15, 2026' or "
             "(contains(@class,'DayPicker-Day') and normalize-space(text())='15' and not(contains(@class,'outside')))]"),
            "June 15 on calendar",
        )

        try:
            pax_done = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'Done') or contains(text(),'Apply')]")
                )
            )
            pax_done.click()
            step("Confirmed passenger count (Done)")
        except TimeoutException:
            pass 

        wait_and_click(
            driver, wait,
            (By.XPATH,
             "//a[contains(@class,'primaryBtn') and (contains(text(),'Search') or contains(text(),'SEARCH'))]"
             " | //button[contains(text(),'Search') or contains(text(),'SEARCH')]"),
            "Search button",
        )

        wait.until(EC.url_contains("flight/search"))
        time.sleep(3)
        dismiss_popup(driver, wait)
        log.info("Search results page loaded.")

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

        dismiss_popup(driver, wait)

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

        end_time = time.time()
        total_seconds = round(end_time - homepage_ready, 2)

        
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