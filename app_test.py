def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Solution cloud-compatible
    try:
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    except WebDriverException as e:
        st.error(f"Erreur ChromeDriver: {str(e)}")
        return None


def scrape_ordi(url):
    driver = None
    try:
        driver = get_driver()
        if not driver:
            return pd.DataFrame()

        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "listing-card__content"))
        )
        
        soup = bs(driver.page_source, "html.parser")
        contenairs = soup.find_all("div", class_="listing-card__content")
        
        data = []
        for content in contenairs:
            item = {
                "Details": content.find("div", class_="listing-card__header__title").get_text(strip=True),
                "Etat": content.find("div", class_="listing-card__header__tags").find_all("span")[0].text,
                "Prix": content.find("div", class_="listing-card__info-bar__price").find("span", class_="listing-card__price__value").get_text(strip=True).replace("F Cfa", ""),
                "Lien_image": content.find("img", class_="listing-card__image__resource")["src"]
            }
            data.append(item)
            
        return pd.DataFrame(data)
        
    except Exception as e:
        st.error(f"Erreur de scraping: {str(e)}")
        return pd.DataFrame()
    finally:
        if driver:
            driver.quit()




if lance_scrap:         
    if categorie == "Ordinateurs":
        df = scrape_ordi(url)
        if not df.empty:
            st.session_state["scraped_data"] = df
            st.dataframe(df)
        else:
            st.warning("Aucune donnée trouvée")

