from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import shutil
from pprint import pprint
from glob import glob
import os
import random

from argparse import ArgumentParser
from configparser import ConfigParser
import logging
from logging.config import dictConfig

from mongo_methods import mongodb_conn, find, updateOne, countDocs, getBUdetails

# Operational configs
# Argparse
parser = ArgumentParser(description='Ferramenta de webscrapping desenvolvida para extrair arquivos de boletins de urna do portal de resultados do TSE.')
parser.add_argument('-l', action='store', dest="limit_exec", required=False, help="Limita o numero de coletas ao valor informado, caso nao especificado, o programa continuara executando em todas as urnas registradas no TSE.")
args = parser.parse_args()

# Cfgparse
config = ConfigParser()
config.read('auditBu.cfg')

# Logging
logging.basicConfig(filename=config.get('default','logfile_getter'), filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Mongodb Connection
mongo_conn = mongodb_conn(config.get('default','mongoString'))
db_conn = mongo_conn[config.get('default','mongoDbName')]


# Funcao de chamada do selenium para efetuar download do log de urna no TSE
def downloadLog(urna, destination_dir):   
    # Validando diretorios
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)

    tmpFileLocation = config.get('default','temporaryFileStore')
    if not os.path.isdir(tmpFileLocation):
        os.mkdir(tmpFileLocation)
    
    servico = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    #options.add_argument('--window-size=1920x1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_experimental_option("prefs",{"download.default_directory" : tmpFileLocation})
    driver = webdriver.Chrome(options=options, service=servico)

    page = 'https://resultados.tse.jus.br/oficial/app/index.html#/eleicao;e=e{};uf={};ufbu={};mubu={};zn={};se={}/dados-de-urna/log-da-urna'.format(urna['CD_ELEICAO'], 
        urna['SG_UF'], urna['SG_UF'], urna['CD_MUNICIPIO'], urna['NR_ZONA'], urna['NR_SECAO'])
    logger.info('Efetuando download do log em ' + page)
    xpath = '/html/body/app-root/ion-app/ion-router-outlet/ng-component/div/div[2]/ng-component/app-dados-de-urna/app-log-da-urna/app-centralizar/div[2]/div[2]/div'


    try:
        driver.get(page)
    except Exception as e:
        logger.error(e)
        return None
    
    driver.refresh()
    delay = int(config.get('default','webDriverWaitSecs'))

    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, xpath)))
        #myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located(By.CSS_SELECTOR, css_selector))
    except TimeoutException:
        logger.warning('Timeout por espera da presenca do xpath element!')
       
    try:
        driver.find_element(By.XPATH, xpath).click()
        #driver.find_element(By.CSS_SELECTOR, css_selector).click()
    except Exception as e:
        logger.error('Falha na chamada ao xPath: ' + str(e))

    time.sleep(1); driver.close
    
    # Obtendo full path do arquivo baixado:
    file = ''
    filesInPath = os.listdir(tmpFileLocation)
    files = [i for i in filesInPath if i.startswith('LogDeUrna') and i.endswith('.zip')]

    if len(files) > 1:
        logger.warning("Mais de um boletim de urna no 'temporaryFileStore'. O mais recente sera utilizado como base. Considere limpar o diretorio.")
        files - glob(tmpFileLocation+'/*.zip')
        file = max(files, key=os.path.getctime)
    elif len(files) == 0: 
        logger.error("Download do arquivo nao realizado: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']))
    else:
        file = files[0]
        logger.info("Download bem sucedido: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']))
  
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)

    if os.path.isfile(tmpFileLocation + file):
        shutil.move(tmpFileLocation + file, destination_dir)
        return file
    else:
        return None


# Lista ordenada alfabeticamente de estados com contagem de urnas:
bu_by_state_list = getBUdetails(db_conn)

if args.limit_exec:
    attempts = int(args.limit_exec)
else:
    attempts = countDocs(db_conn, 'zonas_eleitorais', {'log_obtido': {'$exists': False}})

attempt=0

while attempt < attempts:

    # Obtendo lista de dicionarios de todas urnas do estado:
    filter = {'log_obtido': {'$exists': False}}
    urnas_unsampled = find(db_conn, 'zonas_eleitorais', filter)

    sampling_size = int(config.get('default','samplingSize'))

    if attempts > sampling_size:
        urnas = random.sample(urnas_unsampled, sampling_size)    
    else:
        urnas = random.sample(urnas_unsampled, attempts)    

    # Iterando na lista de urnas:
    for urna in urnas:
        destino = config.get('default','finalFileStoreDir') + urna['SG_UF'] + '-' + urna['NR_ZONA'] + '/'
        result_file_name = downloadLog(urna, destino)
        
        filter = {"_id": urna['_id']}    
        
        if result_file_name and os.path.isfile(destino+result_file_name):
            newvalues = {"log_obtido": 1, "file_name": destino+result_file_name}
            updateOne(db_conn, 'zonas_eleitorais', filter, newvalues)
            print("Sucesso: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']))
            logger.info('Informacao de boletim baixado gravado em banco de dados.')
        else:
            newvalues = {"falhou_download": 1}
            updateOne(db_conn, 'zonas_eleitorais', filter, newvalues)
            print("Falha: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']))
            logger.error('Gravada sinalizacao de falha para download para posterior retentativa de download')

        attempt += 1

print("Processamento concluido")
exit(0)
# EOF