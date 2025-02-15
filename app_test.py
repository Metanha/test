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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
import requests
from requests import get

# 🛠️ Installer Chromium et ChromeDriver (pour Streamlit Cloud)
os.system("apt update && apt install -y chromium-chromedriver")

# ✅ Vérification Selenium et WebDriver
st.write("🔎 Vérification de Selenium et WebDriver...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    st.success("✅ WebDriver fonctionne !")
    driver.quit()
except Exception as e:
    st.error(f"🚨 Erreur WebDriver : {e}")

# ✅ Configuration du driver Selenium
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    try:
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except WebDriverException as e:
        st.error(f"Erreur ChromeDriver : {str(e)}")
        return None

# ✅ Scraping avec Selenium
def scrape_ordi(url):
    driver = get_driver()
    if not driver:
        return pd.DataFrame()

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "listing-card__content"))
        )
        
        soup = bs(driver.page_source, "html.parser")
        contenairs = soup.find_all("div", class_="listing-card__content")
        
        data = []
        for content in contenairs:
            try:
                item = {
                    "Details": content.find("div", class_="listing-card__header__title").get_text(strip=True),
                    "Etat": content.find("div", class_="listing-card__header__tags").find_all("span")[0].text,
                    "Prix": content.find("div", class_="listing-card__info-bar__price").find("span", class_="listing-card__price__value").get_text(strip=True).replace("F Cfa", ""),
                    "Lien_image": content.find("img", class_="listing-card__image__resource")["src"]
                }
                data.append(item)
            except Exception as e:
                st.warning(f"⚠️ Erreur d'extraction : {str(e)}")

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Erreur de scraping: {str(e)}")
        return pd.DataFrame()
    finally:
        driver.quit()

# ✅ Affichage des données
def load_(dataframe, title):
    st.subheader(f'📊 Données : {title}')
    st.write(f'Dimensions: {dataframe.shape[0]} lignes × {dataframe.shape[1]} colonnes')
    st.dataframe(dataframe)

# 🌍 Configuration de la page 
st.set_page_config(page_title="Web Scraping App", layout="wide")

# 🎛️ Barre latérale pour la navigation
menu = st.sidebar.radio("Navigation", ["📊 Scraper des données", "📈 Dashboard des données", "📝 Formulaire d'évaluation"])

# 📊 **Scraper des données**
if menu == "📊 Scraper des données":
    st.title("Scraper des données")
    
    categorie = st.radio("Choisissez les données à scraper :", ["Ordinateurs", "Téléphones", "Télévision"])
    
    col1, col2 = st.columns(2)
    with col1:
        lance_scrap = st.button("🚀 Lancer le scraping")
    with col2:
        telecharger_donne = st.button("📥 Télécharger les données")     

    url = ""
    if categorie == "Ordinateurs":
        url = "https://www.expat-dakar.com/ordinateurs?page=1"
    elif categorie == "Téléphones":
        url = "https://www.expat-dakar.com/telephones?page=1"
    elif categorie == "Télévision":
        url = "https://www.expat-dakar.com/tv-home-cinema?page=1"
    
    if lance_scrap:
        df = scrape_ordi(url)
        if not df.empty:
            st.session_state["scraped_data"] = df
            load_(df, categorie)
        else:
            st.warning("⚠️ Aucune donnée trouvée")

    if telecharger_donne and "scraped_data" in st.session_state:
        csv = st.session_state["scraped_data"].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger le CSV", csv, "donnees_scrapees.csv", "text/csv")

# 📈 **Dashboard des Données Scrapées**
elif menu == "📈 Dashboard des données":
    st.title("📊 Dashboard des Données Scrapées")

    if "scraped_data" in st.session_state and not st.session_state["scraped_data"].empty:
        df = st.session_state["scraped_data"]

        # **Histogramme des Prix**
        st.subheader("📈 Distribution des Prix")
        fig, ax = plt.subplots()
        ax.hist(pd.to_numeric(df["Prix"], errors="coerce").dropna(), bins=20, color="blue", alpha=0.7)
        ax.set_xlabel("Prix (F CFA)")
        ax.set_ylabel("Nombre de produits")
        ax.set_title("Distribution des prix")
        st.pyplot(fig)

        # **Répartition des Marques**
        st.subheader("🎯 Répartition des Marques")
        fig_pie = px.pie(df, names="Etat", title="Répartition des États", hole=0.4)
        st.plotly_chart(fig_pie)

        # **Tableau interactif avec filtres**
        st.subheader("📜 Filtrer les données")
        etat_filter = st.multiselect("Filtrer par état :", df["Etat"].unique())
        if etat_filter:
            df = df[df["Etat"].isin(etat_filter)]
        st.dataframe(df)
    else:
        st.warning("⚠️ Aucune donnée disponible. Faites d'abord un scraping.")

# 📝 **Formulaire d'évaluation**
elif menu == "📝 Formulaire d'évaluation":
    st.title("📝 Formulaire d'évaluation")
    kobo_link = '<iframe src="https://ee.kobotoolbox.org/i/TOv0huae" width="800" height="600"></iframe>'
    st.markdown(kobo_link, unsafe_allow_html=True)
