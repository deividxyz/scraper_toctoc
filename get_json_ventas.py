from seleniumwire import webdriver

""" 
Importamos Selenium-Wire. Permite inspeccionar los requerimientos a nivel de red (XHRs)
Es un poco más lentito porque debe sacar el SSL de los sitios web con un proxy.
"""

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import csv
import json
import time, sys
import warnings
import os
import argparse
from pathlib import Path

if not sys.warnoptions:
    warnings.simplefilter("ignore")

pwd = os.getcwd()

""" 
Por defecto este script está pensado para Chrome (chromedriver)
En este bloque lo configuramos para que no cargue imagenes y para que corra en modo headless
"""

option = webdriver.ChromeOptions()
chrome_prefs = {}
option.experimental_options["prefs"] = chrome_prefs
option.add_argument("--headless") # descomentar cuando no se quiera ver la salida
chrome_prefs["profile.default_content_settings"] = {"images": 2}
chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}

"""
Definimos opciones en este bloque
archivo_links: ruta al archivo .csv de los links, creado por el otro script
salida: nombre de carpeta en donde se guardarán los JSON descargados. Si no existe, será creada. Por defecto, se guarda en la misma ruta del script. 
"""

parser = argparse.ArgumentParser(description="Procesa la lista de links TocToc hacia archivos JSON")
parser.add_argument('archivo_links', type=str, help='Ruta archivo .csv de la lista de links TocToc. Ejemplo: "~/Downloads/stgo_rm.csv" (en comillas).')
parser.add_argument('salida', type=str, help='Ruta a la carpeta de salida. Ejemplo: "~/Downloads/Santiago - RM" (en comillas).')

args = parser.parse_args()

archivo_links = args.archivo_links
salida = args.salida
timeout = 30 # timeout que despu

ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,) # ignoramos estas excepciones al hacer esperar el coso

Path(salida + '/nuevas/').mkdir(parents=True,exist_ok=True)
Path(salida + '/usadas/').mkdir(parents=True,exist_ok=True)

driver = webdriver.Chrome(chrome_options=option)

driver.scopes = [
    '.*toctoc.*'
]

with open(archivo_links) as archivo:

    csv_reader = csv.reader(archivo)

    for fila in csv_reader:

        url = fila[0]

        # extractor de id de aviso (el numerito), para cotejar con link del api toctoc

        loc = 0
        for letra in url:
            if letra == '?':
                break
            loc = loc + 1

        id_aviso = url[:loc] # url cortado hasta el numerito

        loc = 0
        for letra in reversed(id_aviso):
            if letra == '/':
                break
            loc = loc + 1

        id_aviso = id_aviso[-loc:] # el id aviso propiamente tal

        # debemos buscar según la clase el link esperado del api

        url_api_esperado = ''

        # clasificamos avisos (nuevo/usado)

        if ('/compranuevo/' in url) and 'compraparticular' not in url and 'compracorredoras' not in url:
            nuevo = 1
            url_api_esperado = 'https://www.toctoc.com/api/propiedad/nueva/compra-nuevo?id=' + str(id_aviso) # propiedad nueva
        else:
            nuevo = 0
            url_api_esperado = 'https://www.toctoc.com/api/propiedades/usadas/' + str(id_aviso) # propiedad usada

        # ejemplo de solicitud

        # verificamos si el id no lo hemos descargado anteriormente

        if nuevo == 1 and os.path.isfile('./' + salida + '/nuevas/' + str(id_aviso) + '.json') == True:
            print('Propiedad nueva id ' + str(id_aviso) + ' ya fue descargada, saltando ...')
            pass

        elif nuevo == 0 and os.path.isfile('./' + salida + '/usadas/' + str(id_aviso) + '.json') == True:
            print('Propiedad usada id ' + str(id_aviso) + ' ya fue descargada, saltando ...')
            pass

        else:

            try:
                driver.get(url)
                respuesta_raw = driver.wait_for_request(url_api_esperado,timeout=timeout).response.body # json (según el tipo de propiedad). Profit.
                respuesta_json = json.loads(respuesta_raw.decode('utf8'))

                if nuevo == 1:

                    print('Guardando JSON propiedad nueva, id ' + str(id_aviso) + ' ...')
                    with open(salida + '/nuevas/'+str(id_aviso) + '.json','w') as salida_json:
                        json.dump(respuesta_json,salida_json,ensure_ascii=False)
                else:
                    print('Guardando JSON propiedad usada, id ' + str(id_aviso) + ' ...')
                    with open(salida + '/usadas/' + str(id_aviso) + '.json','w') as salida_json:
                        json.dump(respuesta_json,salida_json,ensure_ascii=False)

                # el json obtenido tiene toda la data de los avisos!

            except TimeoutException:
                if nuevo == 1:
                    print('Timeout en propiedad nueva id ' + id_aviso + ', url culpable: ' + url)
                else:
                    print('Timeout en propiedad usada id ' + id_aviso + ', url culpable: ' + url)
                pass

archivo.close()
driver.close()

