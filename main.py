from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import random

INGREDIENTS_FILE = "ingredients.txt"

# Use this method the first time you run to save/load cookies for Amazon/Bing so you can be logged in.
def save_cookie(driver, path):
    with open(path, 'w') as filehandler:
        json.dump(driver.get_cookies(), filehandler)

def load_cookie(driver, path):
    with open(path, 'r') as cookiesfile:
        cookies = json.load(cookiesfile)
    for cookie in cookies:
        driver.add_cookie(cookie)

# types at a regular speed.
# i have absolutely no idea if amazon does bot detection or anything but i don't want to find out
def real_human_type(elt, text):
    for c in text:
        elt.send_keys(c)
        time.sleep(random.randint(1, 15) / 100) # sleep a bit between keypresses

def highlight(driver, elt, style="background: yellow; border: 3px solid red;"):
    driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", elt, style)

def load_ingredients(path=INGREDIENTS_FILE):
    with open(INGREDIENTS_FILE, "r") as f:
        ingredients = f.readlines()
        ingredients = [i.strip() for i in ingredients]
        return ingredients
    
def get_ingredients():
    baseIngredients = load_ingredients()
    # filter out common ingredients i have already
    excludeList = [
        "salt",
        "pepper",
        "olive oil",
        "extra-virgin olive oil",
        "garlic",
        "garlic cloves",
        "garlic powder",
        "cumin",
        "paprika",
        "smoked paprika",
        "honey"
    ]
    ingredients = [ i for i in baseIngredients if i.lower() not in excludeList ] # would be way faster to do this with sets but eh
    return ingredients

def order(driver):
    print("Starting ordering process.")
    ingredients = get_ingredients()
    print(ingredients)

    print("OK NOW IT IS TIME TO GO TO AMAZON AND ORDER")
    driver.get("https://www.amazon.com/alm/storefront?almBrandId=VUZHIFdob2xlIEZvb2Rz")
    load_cookie(driver, "cookies.json")

    if True:
        for i in ingredients:
            time.sleep(5)
            searchbar = driver.find_element(By.XPATH, "//input[@placeholder='Search Amazon']")
            searchbar.clear()
            print(f"Searching for {i}")
            real_human_type(searchbar, i)
            searchbar.send_keys(Keys.RETURN)

            # Make sure product container isn't an ad
            productContainers = driver.find_elements_by_class_name("s-card-container")
            for p in productContainers:
                # ignore sponsored
                if "Sponsored" not in p.get_attribute('innerHTML'):
                    # sanity check that this is probably the right ingredient
                    highlight(driver, p)
                    try:  # may not exist, "choose quantity" button is different
                        atcButton = p.find_element_by_class_name("a-button-primary")
                        highlight(driver, atcButton, style="background: green; border: 3px solid red;")
                        atcButton.click()
                        break
                    except:
                        # if this is choose quantity, wait for page load then find the cart button
                        try:
                            quantityButton = p.find_element_by_class_name("a-button-text")
                            highlight(driver, quantityButton)
                            quantityButton.click()
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.ID, "freshAddToCartButton-announce"))
                            )
                            driver.find_element_by_id("freshAddToCartButton").click()
                            break
                        finally:
                            pass # give up if that didn't work


    cartButton = driver.find_element_by_id("nav-cart")
    highlight(driver, cartButton, style="background: green; border: 3px solid red;")
    cartButton.click()
    time.sleep(3)
    # next go to checkout
    driver.find_element_by_class_name("a-button-input").click()
    time.sleep(3)
    
    # maybe not always interstitial?
    try:
        driver.find_element_by_class_name("byg-continue-button").find_element_by_tag_name("a").click()
    except:
        pass

    print("Waiting")
    time.sleep(7)

    # after that substition menu
    driver.find_element_by_id("subsContinueButton").find_element_by_tag_name("input").click()
    print("Waiting on time slot selection")
    time.sleep(7)

    # after that, time slot pick menu, just take next
    # driver.find_element_class_name("ufss-slot-toggle-native-button") is query if next timeslot not desired
    driver.find_element_by_id("orderSummaryPrimaryActionBtn").click() # go to order summary

    print("Waiting")
    time.sleep(7)

    # MAYBE a credit card confirm button here
    try:
        driver.find_element_by_id("orderSummaryPrimaryActionBtn").click()
        print("clicked cc confirm")
    except:
        print("no cc confirm")
        pass
    
    time.sleep(7)


    submitButton = driver.find_element_by_id("submitOrderButtonId")
    print(submitButton)
    # DANGER DANGER DO NOT UNCOMMENT THIS CLICK unless you want to submit for real and actually pay real money
    ### submitButton.click()
    print("READY TO SUBMIT!")


def chat(driver):
    driver.get("https://www.bing.com")
    load_cookie(driver, "bingcookies.json")
    driver.get("https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=HDRSC2")
    time.sleep(5)
    # SHADOW ROOT AAAH
    searchBox = driver.execute_script("""return document.querySelector('.cib-serp-main').shadowRoot.querySelector("#cib-action-bar-main").shadowRoot.querySelector("#searchbox")""")
    prompt = "Suggest one healthy dinner recipe that I can prepare in less than 30 minutes. Use only ingredients that can be commonly found at a regular grocery store. I am deathly allergic to seafood, mushrooms, and eggplant, so UNDER NO CIRCUMSTANCES should these ingredients be included. DO NOT SUGGEST WALNUT-ROSEMARY CRUSTED SALMON. List out the ingredients with quantities as bullet points and the method for preparing the meal in numbered steps. Do not respond with a question, follow the output format I have specified. End your response with 'RESPONSE FINISHED'."
    prompt2 = "From the above recipe, output a shopping list of ingredients. Do not include any quantities for ingredients or preparation instructions, I just want a list of the basic ingredients. I don't care if the ingredients are organic or healthy, so leave adjectives like 'organic', 'whole wheat' or 'low-fat' out. Leave out optional ingredients and any cooking oils or sprays. End your response with 'RESPONSE FINISHED'."

    searchBox.send_keys(prompt)
    searchBox.send_keys(Keys.RETURN)

    docQuery1 = """return document.querySelector('.cib-serp-main').shadowRoot.querySelector("#cib-conversation-main").shadowRoot.querySelectorAll("cib-chat-turn")[1].shadowRoot.querySelector(".response-message-group").shadowRoot.querySelectorAll("cib-message")[2].shadowRoot.querySelector(".ac-textBlock").innerText"""

    time.sleep(20)

    response1 = driver.execute_script(docQuery1)
    while True:
        response1 = driver.execute_script(docQuery1)
        time.sleep(3)
        if "RESPONSE FINISHED" in response1:
            break


    print("Done with part 1.")
    # click stop responding so we can send new prompt
    stopButton = driver.execute_script("""return document.querySelector('.cib-serp-main').shadowRoot.querySelector("#cib-action-bar-main").shadowRoot.querySelector("cib-typing-indicator").shadowRoot.querySelector("#stop-responding-button")""")
    if stopButton and stopButton.is_enabled():
        stopButton.click()

    time.sleep(1)
    searchBox.send_keys(prompt2)
    time.sleep(1)
    searchBox.send_keys(Keys.RETURN)
    
    time.sleep(20)

    docQuery2 = """ return document.querySelector('.cib-serp-main').shadowRoot.querySelector("#cib-conversation-main").shadowRoot.querySelectorAll("cib-chat-turn")[2].shadowRoot.querySelector(".response-message-group").shadowRoot.querySelector("cib-message").shadowRoot.querySelector(".ac-textBlock").innerText"""

    response2 = driver.execute_script(docQuery2)
    while True:
        response2 = driver.execute_script(docQuery2)
        time.sleep(3)
        if "RESPONSE FINISHED" in response2:
            break

    print("DONEZO")
    print("First response: ", response1)
    print("Shopping list: ", response2)

    with open("recipe.txt", "w") as f:
        f.write(response1)

    with open(INGREDIENTS_FILE, "w") as f:
        response2 = response2.replace("RESPONSE FINISHED", "")
        responseLines = response2.split("\n")[1:] # get rid of first line, chatgpt usually includes some fluff
        responseLines = [r for r in responseLines if len(r) > 0]
        print(responseLines)
        f.write("\n".join(responseLines))

    print("OK, done with getting recipe from chat.")



def main():
    driver = webdriver.Edge(executable_path="./edgedriver/msedgedriver.exe")
    # Regular runs
    if True:
        chat(driver)
        order(driver)
    # First time setup:
    # - Set above boolean to false
    # - Start driver, then manually navigate to bing, sign in, go to chat page.
    # - Wait for cookies to save.
    # - Do the same for amazon; manually navigate and sign in, wait for cookies to save.
    else:
        print("GO SIGN IN TO BING! 60 seconds to do so.")
        time.sleep(60)
        save_cookie(driver, "bingcookies.json")
        print("SAVED BING COOKIES (hopefully)!")
        print("GO SIGN IN TO AMAZON! 60 seconds to do so.")
        time.sleep(60)
        save_cookie(driver, "cookies.json")


main()

