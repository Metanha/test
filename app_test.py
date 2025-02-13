import os
import streamlit as st
import pandas as pd
import time
import matplotlib.pyplot as plt
import plotly.express as px
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
import requests
from requests import get

# Installer Chromium et ChromeDriver
os.system("apt update")
os.system("apt install -y chromium-chromedriver")

# Définir les chemins d'accès pour Selenium
os.environ["CHROME_BINARY"] ="/home/appuser/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver"
os.environ["webdriver.chrome.driver"] ="/home/appuser/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver"

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
    
    #service = Service(ChromeDriverManager().install())
    #return webdriver.Chrome(service=service, options=chrome_options)

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

def load_(dataframe, title):
    st.markdown("""
    <style>
    div.stButton {text-align:center}
    </style>""", unsafe_allow_html=True)

    #if st.button(title, key):
    st.subheader('Display data dimension')
    st.write('Data dimension: ' + str(dataframe.shape[0]) + ' rows and ' + str(dataframe.shape[1]) + ' columns.')
    st.dataframe(dataframe)

# Configuration de la page 
st.set_page_config(page_title="Web Scraping App", layout="wide")

# Barre latérale pour la navigation
menu = st.sidebar.radio("Navigation", ["📊 Scraper des données", "📈 Dashboard des données", "📝 Formulaire d'évaluation"])

# 📊 **Scraper des données**
if menu == "📊 Scraper des données":
    st.title("Scraper des données")
    
    categorie=st.radio("Choisissez les données à scrapper ",["Ordinateurs","Téléphones","Télévision"])
    #url = st.text_input("Entrez l'URL de la page à scraper :", "")
    #Creation de deux colonnes pour aligner les boutons sur la même ligne  
    col1,col2=st.columns(2)
    with col1:
        lance_scrap=st.button("Lancer le scraping")
    with col2:
            telecharger_donne=st.button("📥 Télécharger les données")     
       # Sélection du nombre de pages
    url=""
    if categorie=="Ordinateurs":
        url="https://www.expat-dakar.com/ordinateurs?page=1"
        num_pages = st.sidebar.slider("Nombre de pages à scraper :", 1, 10, 1)
    elif categorie=="Téléphones":
        url="https://www.expat-dakar.com/telephones?page=1"
        num_pages = st.sidebar.slider("Nombre de pages à scraper :", 1, 11, 1)
    elif categorie=="Télévision":
        url="https://www.expat-dakar.com/tv-home-cinema?page=1"
        num_pages = st.sidebar.slider("Nombre de pages à scraper :", 1, 12, 1)
    
    if lance_scrap:            
        if categorie == "Ordinateurs":
            df = scrape_ordi(url)
            if not df.empty:
                st.session_state["scraped_data"] = df
                st.dataframe(df)
            else:
                st.warning("Aucune donnée trouvée")
        elif categorie=="Téléphones":
            print()
            #df=scrape_dynamic_site(url)
            #load_(df,"Téléphones")
        elif categorie=="Télévision":
            print()
            #df=scrape_dynamic_site(url)
            #load_(df,"Télévision")
    
     #Telecharger les données scrappées  
    if telecharger_donne:
        csv = df.to_csv(path_or_buf="data/donnees_scrapes.csv",index=False).encode('utf-8')




# 📈 **Dashboard des Données Scrapées**
elif menu == "📈 Dashboard des données":
    st.title("📊 Dashboard des Données Scrapées")

    if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
        df = st.session_state["scraped_data"]

        # **Histogramme des Prix**
        st.subheader("📈 Distribution des Prix")
        fig, ax = plt.subplots()
        ax.hist(df["Prix"], bins=20, color="blue", alpha=0.7)
        ax.set_xlabel("Prix (F CFA)")
        ax.set_ylabel("Nombre de produits")
        ax.set_title("Distribution des prix")
        st.pyplot(fig)

        # **Répartition des Marques**
        st.subheader("🎯 Répartition des Marques")
        fig_pie = px.pie(df, names="Marque", title="Répartition des Marques", hole=0.4)
        st.plotly_chart(fig_pie)

        # **Comparaison des prix par marque**
        st.subheader("💰 Comparaison des Prix par Marque")
        fig_bar = px.bar(df, x="Marque", y="Prix", title="Prix moyen par marque", color="Marque", barmode="group")
        st.plotly_chart(fig_bar)

        # **Tableau interactif avec filtres**
        st.subheader("📜 Table des Données Filtrables")
        marque_filter = st.multiselect("Filtrer par Marque :", df["Marque"].unique())
        if marque_filter:
            df = df[df["Marque"].isin(marque_filter)]
        st.dataframe(df)
    else:
        st.warning("Aucune donnée disponible. Faites d'abord un scraping.")

# 📝 Formulaire d'évaluation**
elif menu == "📝 Formulaire d'évaluation":
    st.title("📝 Formulaire d'évaluation")
    
    #kobo_link = "<iframe src=https://ee.kobotoolbox.org/i/TOv0huae width="800" height="600"></iframe>"
    st.markdown(f'<iframe src=https://ee.kobotoolbox.org/i/TOv0huae width="800" height="600"></iframe>', unsafe_allow_html=True)


