from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import os
import shutil
from tqdm import tqdm
from pprint import pprint

from mongo_methods import find, updateOne, mongodb_conn, getBUdetails

# Mongodb Connection
mongo_conn = mongodb_conn('mongodb://localhost:27017/')
db_conn = mongo_conn["audit_eleicao_2022"]


# Funcao de chamada do selenium para efetuar download do log de urna no TSE
def downloadLog(urna, destination_dir):   
    # Validando diretorios
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)

    tmpFileLocation = '/tmp/logUrna/'
    if not os.path.isdir(tmpFileLocation):
        os.mkdir(tmpFileLocation)
    
    servico = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_experimental_option("prefs",{"download.default_directory" : tmpFileLocation})
    driver = webdriver.Chrome(options=options, service=servico)

    page = 'https://resultados.tse.jus.br/oficial/app/index.html#/eleicao;e=e{};uf={};ufbu={};mubu={};zn={};se={}/dados-de-urna/log-da-urna'.format(urna['CD_ELEICAO'], 
        urna['SG_UF'], urna['SG_UF'], urna['CD_MUNICIPIO'], urna['NR_ZONA'], urna['NR_SECAO'])
    xpath = '/html/body/app-root/ion-app/ion-router-outlet/ng-component/div/div[2]/ng-component/app-dados-de-urna/app-log-da-urna/app-centralizar/div[2]/div[2]/div'
    
    driver.get(page)
    driver.refresh()
    delay = 10
    
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element(By.XPATH, xpath).click()
    except TimeoutException:
        print('Loading took too much time!')
        
    # Obtendo full path do arquivo baixado:
    file = ''
    filesInPath = os.listdir(tmpFileLocation)
    files = [i for i in filesInPath if i.startswith('LogDeUrna') and i.endswith('.zip')]

    if len(files) > 0:
        file = files[0]
        if not os.path.isdir(destination_dir):
            os.mkdir(destination_dir)
        shutil.move(tmpFileLocation + file, destination_dir)
      
    return file


# Lista ordenada alfabeticamente de estados com contagem de urnas:
bu_by_state_list = getBUdetails(db_conn)

for state in bu_by_state_list:
    # Obtendo lista de dicionarios de todas urnas do estado:
    filter = {'SG_UF': state['_id'], 'log_obtido': {'$exists': False}}
    urnas = find(db_conn, 'zonas_eleitorais', filter)

    # Iterando na lista de urnas:
    for urna in tqdm(urnas):
    #for urna in tqdm(urnas[0:1]):
        destino = '/home/jobernardes/Documents/Projects/auditBU/database/logs/' + urna['SG_UF'] + '-' + urna['NR_ZONA'] + '/'
        result_file_name = downloadLog(urna, destino)
        filter = {"_id": urna['_id']}
        
        if result_file_name and os.path.isfile(destino+result_file_name):
            newvalues = {"log_obtido": 1}
            updateOne(db_conn, 'zonas_eleitorais', filter, newvalues)
        else:
            newvalues = {"falhou_download": 1}
            updateOne(db_conn, 'zonas_eleitorais', filter, newvalues)

    print("Processamento do estado ", state['_id'] ,"finalizado.")
    #break

print("Processamento concluido")
# EOF