from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = webdriver.Chrome()
driver.maximize_window()

steps = 0

def click(el):
    global steps
    el.click()
    steps += 1

def type_text(el, text):
    global steps
    el.send_keys(text)
    steps += 1

start_time = time.time()

driver.get("https://www.makemytrip.com/")
time.sleep(5)

# Close popup
wait = WebDriverWait(driver, 15)

# Wait for page to load and click somewhere safe
wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
driver.execute_script("document.body.click();")

# FROM
click(driver.find_element(By.ID, "fromCity"))
input_box = driver.find_element(By.XPATH, "//input[@placeholder='From']")
type_text(input_box, "Hyderabad")
time.sleep(2)
input_box.send_keys(Keys.ENTER)

# TO
click(driver.find_element(By.ID, "toCity"))
input_box = driver.find_element(By.XPATH, "//input[@placeholder='To']")
type_text(input_box, "Delhi")
time.sleep(2)
input_box.send_keys(Keys.ENTER)

# DATE
click(driver.find_element(By.XPATH, "//div[@aria-label='Sun Jun 15 2026']"))

# SEARCH
click(driver.find_element(By.XPATH, "//a[text()='Search']"))
time.sleep(10)

# SORT BY PRICE
click(driver.find_element(By.XPATH, "//span[text()='Price']"))
time.sleep(5)

# SELECT FIRST FLIGHT
click(driver.find_element(By.XPATH, "(//button[contains(text(),'Select')])[1]"))

end_time = time.time()

print("Steps:", steps)
print("Time:", end_time - start_time)

driver.quit()