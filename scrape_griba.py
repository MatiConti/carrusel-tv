import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import traceback

def scrape():
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    try:
        print("Scraping en segundo plano para estudiar el DOM...")
        driver.get("https://paneldpc.griba.com.ar:8443/LoginPage?ReturnUrl=%2FDashboardViewer_DetailView%2F8ba5ecce-fbbc-4850-82a5-738ae855aba9")
        time.sleep(4)
        
        inputs = driver.find_elements(By.TAG_NAME, "input")
        input_usuario = next((i for i in inputs if i.get_attribute("type") in ["text", "email", "", None] and i.is_displayed()), None)
        input_clave = next((i for i in inputs if i.get_attribute("type") == "password" and i.is_displayed()), None)
        
        if input_usuario and input_clave:
            input_usuario.send_keys("mconti")
            time.sleep(1)
            input_clave.send_keys("mconti")
            input_clave.send_keys(Keys.RETURN)
        
        time.sleep(15) # Darle muchísimo tiempo al dashboard
        
        # Recopilar clases e ids de los posibles botones
        widgets = driver.find_elements(By.CSS_SELECTOR, "[class*='dashboard'], svg, [title*='maxi'], [title*='Maxi']")
        
        print("\n\n=== EXTRACCIÓN DE BOTONES DE MAXIMIZAR ===")
        for wp in widgets:
            html = (wp.get_attribute("outerHTML") or "").lower()
            if "maximize" in html or "fullscreen" in html or "ampliar" in html or "expand" in html:
                title = wp.get_attribute("title")
                cls = wp.get_attribute("class")
                if title or (cls and ('button' in cls or 'icon' in cls)):
                    print(f"ELEMENTO ENCONTRADO:\n  -> Tag: {wp.tag_name}\n  -> Class: {cls}\n  -> Title: {title}\n  -> HTML: {html[:350]}\n")
        
        print("======================\nDone Scraping")
    except Exception as e:
        print("Error scraping:", e)
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape()
