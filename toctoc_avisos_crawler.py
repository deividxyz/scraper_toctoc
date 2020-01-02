from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import csv
import time, sys
import warnings
import os

import argparse

if not sys.warnoptions:
    warnings.simplefilter("ignore")

pwd = os.getcwd()

option = webdriver.ChromeOptions()
chrome_prefs = {}
option.experimental_options["prefs"] = chrome_prefs
option.add_argument("--headless") # descomentar cuando no se quiera ver la salida
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

parser = argparse.ArgumentParser(description="Baja los links de avisos desde TocToc.com, dada una ubicación definida.")
parser.add_argument('ubicacion', type=str, help='Ubicación. Ejemplo: "Santiago, Región Metropolitana" (con comillas).')
parser.add_argument('salida', type=str, help='Ruta completa al archivo de salida (.csv), en dónde se guardarán los links. Ejemplo: ./stgo_rm.csv')

args = parser.parse_args()

localizacion_busqueda = args.ubicacion
salida = args.salida

links = []

ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,) # ignoramos estas excepciones al hacer esperar el coso

driver = webdriver.Chrome(chrome_options=option)
driver.get('https://www.toctoc.com/')

driver.implicitly_wait(20)

print('Scraper avisos TocToc.com, deivid.xyz')
print('**************************************')
print('')
print('Buscando actualmente avisos de venta activos en: ' + str(localizacion_busqueda) + '.')
print('')

caja_busqueda = driver.find_elements_by_xpath('//*[@id="boxBuscador"]/input')[0]

caja_busqueda.send_keys(localizacion_busqueda)
caja_busqueda.send_keys(u'\ue007')

boton_lista = driver.find_elements_by_xpath('/html/body/main/div[1]/div/div[3]/button')[0].click()

timeout = 15

try:

    while True:

        xpath_avisos = '//*[@id="resul"]//ul//div/a' # avisos (deberían ser 30 por página)
        xpath_sgte = '//*[@id="resul"]/nav/ul/li[1]'

        waiteo = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath_sgte)))
        time.sleep(5)
        avisos = driver.find_elements_by_xpath(xpath_avisos)

        for aviso in avisos:
            print(aviso.get_attribute('href'))
            links.append(aviso.get_attribute('href'))

        time.sleep(3)
        driver.find_element_by_xpath("//*[text() = '›']").click()

except TimeoutException:
    print("Nos quedamos cortitos de tiempo pue ...")

except NoSuchElementException:
    print("No hay más elementos, cerrando ...")

except KeyboardInterrupt:
    print("Saliendo ... ")
    time.sleep(5)

print("Guardando links descargados ... ")

with open(salida, mode='w') as archivo_salida:
    salida = csv.writer(archivo_salida)
    for link in links:
        salida.writerow([link])

    archivo_salida.close()

driver.close()