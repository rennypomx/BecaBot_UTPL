"""
Servicio de web scraping de becas UTPL.
Adaptado de utils/web_scraper.py para Django.
"""

import json
import os
import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logger
logger = logging.getLogger(__name__)


class ScraperService:
    """
    Servicio para realizar scraping de becas desde becas.utpl.edu.ec.
    Mantiene la lógica original exacta.
    """
    
    def __init__(self, save_path="knowledge_base/corpus_utpl.json"):
        self.save_path = save_path
        self.url_base = "https://becas.utpl.edu.ec/"
    
    def _configurar_driver(self):
        """Configura y retorna el driver de Selenium."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    
    def _procesar_metadatos(self, lista_clases):
        """Traduce las clases CSS a texto legible."""
        clases_set = set(lista_clases)
        
        mapa_tipos = {
            'Excelencia': 'Beca de Excelencia',
            'Inclusión': 'Beca de Inclusión',
            'Estratégica': 'Beca Estratégica',
            'Apoyo': 'Beca de Apoyo Económico',
            'Meritos': 'Méritos Universitarios',
            'Convenios': 'Convenios Institucionales'
        }
        
        mapa_modalidades = {
            'Presencial': 'Presencial',
            'Distancia': 'Abierta y a Distancia',
            'Linea': 'En Línea'
        }
        
        tipos = [v for k, v in mapa_tipos.items() if k in clases_set]
        modalidades = [v for k, v in mapa_modalidades.items() if k in clases_set]
        
        return tipos, modalidades
    
    def _parsear_detalle_estructurado(self, soup):
        """
        Extrae la información en formato diccionario buscando pares Label-Valor.
        """
        detalles = {}
        
        region = soup.find('div', class_='region-content') or soup.find('div', class_='content')
        if not region:
            return {"Nota": "No se detectó el contenedor principal de contenido."}
        
        # Estrategia A: Buscar estructura de campos 'field'
        campos = region.find_all('div', class_=lambda x: x and 'field' in x.split())
        
        found_structure = False
        for campo in campos:
            etiqueta_div = campo.find('div', class_='field-label')
            items_div = campo.find('div', class_='field-items')
            
            if etiqueta_div and items_div:
                key = etiqueta_div.get_text(strip=True).rstrip(':')
                value = items_div.get_text(separator='\n', strip=True)
                detalles[key] = value
                found_structure = True
        
        # Estrategia B: Tablas HTML
        if not found_structure:
            filas = region.find_all('tr')
            for fila in filas:
                cols = fila.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).rstrip(':')
                    val = cols[1].get_text(separator='\n', strip=True)
                    detalles[key] = val
                    found_structure = True
        
        # Estrategia C: Fallback a texto plano
        if not found_structure:
            return {"Información General": region.get_text(separator='\n', strip=True)}
        
        return detalles
    
    def scrape_becas(self):
        """
        Función principal de scraping.
        
        Returns:
            Tupla (success: bool, num_becas: int, error_message: str)
        """
        msg = f"🚀 Iniciando scraping en {self.url_base}..."
        print(msg, flush=True)
        logger.info(msg)
        
        driver = None
        lista_becas = []
        
        try:
            driver = self._configurar_driver()
            msg = "Driver de Selenium configurado"
            print(msg, flush=True)
            logger.info(msg)
            
            driver.get(self.url_base)
            time.sleep(5)
            msg = "Página principal cargada"
            print(msg, flush=True)
            logger.info(msg)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # PASO 1: Obtener lista de enlaces
            secciones = {
                'grado': 'Grado',
                'posgrado': 'Posgrado',
                'tecnologia': 'Tecnologías'
            }
            
            for clase_sec, nombre_nivel in secciones.items():
                contenedor = soup.find('div', class_=clase_sec)
                if not contenedor:
                    continue
                
                items = contenedor.find_all('div', class_='item')
                msg = f"   📌 {nombre_nivel}: {len(items)} becas encontradas."
                print(msg, flush=True)
                logger.info(msg)
                
                for item in items:
                    enlace = item.find('a')
                    if enlace:
                        url_relativa = enlace.get('href')
                        url_completa = (
                            self.url_base + url_relativa 
                            if url_relativa and not url_relativa.startswith('http') 
                            else url_relativa
                        )
                        
                        tipos, mods = self._procesar_metadatos(item.get('class', []))
                        
                        lista_becas.append({
                            "titulo": enlace.get_text(strip=True),
                            "url": url_completa,
                            "nivel": nombre_nivel,
                            "tipos": tipos,
                            "modalidades": mods,
                            "contenido": {}
                        })
            
            # PASO 2: Enriquecer con detalle
            total = len(lista_becas)
            msg = f"📥 Descargando detalles de {total} becas..."
            print(msg, flush=True)
            logger.info(msg)
            
            for i, beca in enumerate(lista_becas):
                msg = f"   [{i+1}/{total}] {beca['titulo']}"
                print(msg, flush=True)
                logger.info(msg)
                
                try:
                    driver.get(beca['url'])
                    time.sleep(1.5)
                    soup_detalle = BeautifulSoup(driver.page_source, 'html.parser')
                    beca['contenido'] = self._parsear_detalle_estructurado(soup_detalle)
                
                except Exception as e:
                    error_msg = f"   ⚠️ Error en {beca['url']}: {e}"
                    print(error_msg, flush=True)
                    logger.warning(error_msg)
                    beca['contenido'] = {"Error": "No se pudo extraer contenido."}
            
            # GUARDADO
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(lista_becas, f, ensure_ascii=False, indent=4)
            
            msg = f"✅ Scraping completado. {total} becas guardadas en: {self.save_path}"
            print(msg, flush=True)
            logger.info(msg)
            return True, total, None
        
        except Exception as e:
            error_msg = f"Error crítico en el scraping: {str(e)}"
            print(f"❌ {error_msg}", flush=True)
            logger.error(error_msg, exc_info=True)
            return False, 0, error_msg
        
        finally:
            if driver:
                driver.quit()
                msg = "Driver cerrado"
                print(msg, flush=True)
                logger.info(msg)
    
    def corpus_exists(self):
        """Verifica si el corpus ya existe."""
        return os.path.exists(self.save_path)
    
    def get_corpus_info(self):
        """
        Obtiene información sobre el corpus existente.
        
        Returns:
            Diccionario con información o None si no existe
        """
        if not self.corpus_exists():
            return None
        
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            return {
                'num_becas': len(data),
                'file_size': os.path.getsize(self.save_path),
                'last_modified': os.path.getmtime(self.save_path)
            }
        
        except Exception as e:
            print(f"⚠️ Error al leer corpus: {e}")
            return None
