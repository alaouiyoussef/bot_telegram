import json
import os
import re
import time
from httpx import options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
 
URL = "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"
 
def start_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    if os.environ.get("RAILWAY_ENVIRONMENT"):
        options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
        driver = webdriver.Chrome(
            service=Service(os.environ.get("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")),
            options=options,
        )
    else:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
    return driver
 
 
def category(driver, wait):
    domaine = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="ctl0_CONTENU_PAGE_AdvancedSearch_domaineActivite_linkDisplay"]')
        )
    )
    domaine.click()
    wait.until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[1])
    categorie = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="ctl0_CONTENU_PAGE_repeaterCategorie_ctl2_repeaterSousCategorie_ctl9_idSection"]')
        )
    )
    categorie.click()
    valider = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="ctl0_CONTENU_PAGE_validateButton"]'))
    )
    valider.click()
    driver.switch_to.window(driver.window_handles[0])
 
 
def lancer(driver, wait):
    lancer_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche"]')
        )
    )
    lancer_btn.click()
    select_element = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="ctl0_CONTENU_PAGE_resultSearch_listePageSizeTop"]')
        )
    )
    Select(select_element).select_by_visible_text("100")
    time.sleep(2)
 
 
def nettoyer(texte):
    texte = re.sub(r'\s+', ' ', texte)   
    texte = texte.replace('...', '')      
    return texte.strip()
 
 
def extraire_objet(texte):
    match = re.search(r'Objet\s*:\s*(.+?)(?:Acheteur public|$)', texte, re.DOTALL)
    if match:
        return nettoyer(match.group(1))
    return nettoyer(texte)
 
 
def extraire_acheteur(texte):
    match = re.search(r'Acheteur public\s*:\s*(.+?)$', texte, re.DOTALL)
    if match:
        return nettoyer(match.group(1))
    return ""
 
 
def extraire_type_et_date(texte):
    type_match = re.search(r'(Appel[^\.]+)', texte)
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', texte)
    type_appel = nettoyer(type_match.group(1)) if type_match else ""
    date_pub   = date_match.group(1) if date_match else ""
    return type_appel, date_pub
 
def extraire_lieu(texte):
    parties = [p.strip() for p in texte.split('\n') if p.strip() and p.strip() != '...']
    if parties:
        return max(parties, key=len)
    return nettoyer(texte)
 
 
def extraire_date_limite(texte):
    match = re.search(r'(\d{2}/\d{2}/\d{4})(\d{2}:\d{2})', texte)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    match2 = re.search(r'(\d{2}/\d{2}/\d{4})', texte)
    return match2.group(1) if match2 else nettoyer(texte)
 
 
def recuperer(driver):
    html  = driver.page_source
    soup  = BeautifulSoup(html, "lxml")
    table = soup.select_one("#tabNav div:nth-child(2) div:nth-child(2) table")
    rows  = table.select("tr")[1:]
    results = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 4:
            col_titre    = cols[1].text
            col_org      = cols[2].text
            col_lieu     = cols[3].text
            col_date     = cols[4].text
 
            type_appel, date_pub = extraire_type_et_date(col_titre)
 
            results.append({
                "type":            type_appel,
                "date_publication": date_pub,
                "objet":           extraire_objet(col_org),
                "acheteur":        extraire_acheteur(col_org),
                "lieu":            extraire_lieu(col_lieu),
                "date_limite":     extraire_date_limite(col_date),
            })
    return results
 
 
def save_json(data):
    with open("marches.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
 
 
def main():
    driver = start_driver()
    wait   = WebDriverWait(driver, 20)
    driver.get(URL)
 
    category(driver, wait)
    lancer(driver, wait)
 
    print("Scraping page : 1")
    all_results = recuperer(driver)
    save_json(all_results)
    print(f"{len(all_results)} annonce(s) récupérée(s).")
 
    driver.quit()
    print("Scraping terminé.")
 
 
if __name__ == "__main__":
    main()