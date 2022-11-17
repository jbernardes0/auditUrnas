from configparser import ConfigParser
import logging
from mongo_methods import mongodb_conn, insertOne, updateOne, find, unsetOne

from datetime import datetime
from bson.timestamp import Timestamp

import os, zipfile
import shutil
from pyunpack import Archive
from pprint import pprint

# Cfgparse
config = ConfigParser()
config.read('auditBu.cfg')

# Logging
logging.basicConfig(filename=config.get('default','logfile_digestor'), filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Mongodb Connection
mongo_conn = mongodb_conn(config.get('default','mongoString'))
db_conn = mongo_conn[config.get('default','mongoDbName')]

# Static vars
election_date = config.get('default','election_date')



def digestFile(urna, file_to_read, db_conn):

    first_vote = datetime.strptime('{} 00:00:00'.format(election_date), '%d/%m/%Y %H:%M:%S')
    number_of_votes = 0

    with open(file_to_read, 'r', encoding="latin-1") as f:
        for line in f.readlines():
            if election_date in line:
                if 'Urna pronta para receber votos' in line:
                    first_vote = datetime.strptime(line[:19], '%d/%m/%Y %H:%M:%S')
                if 'Dedo reconhecido e o score para habilitá-lo' in line:
                    usa_biometria = 1

    with open(file_to_read, 'r', encoding="latin-1") as f:
        prev_ts = first_vote
        for line in f.readlines():
            if election_date in line and 'O voto do eleitor foi computado' in line:
                vote_ts = datetime.strptime(line[:19], '%d/%m/%Y %H:%M:%S')
                secs_elaps = vote_ts - prev_ts
                secs_elaps = secs_elaps.total_seconds()
                
                logger.info("Persisting vote: " + str(secs_elaps) + '-' + str(vote_ts))

                merge_dict = {
                    'usa_biometria': usa_biometria,
                    'prev_vote_ts': Timestamp(int(prev_ts.timestamp()),1),
                    'vote_ts': Timestamp(int(vote_ts.timestamp()),1),
                    'secs_elaps': secs_elaps
                }
                voteDict = urna
                voteDict.update(merge_dict)
                voteDict.pop("_id")
                coll = "resultados_de_urna"
                insertOne(db_conn, coll, voteDict)

                prev_ts = vote_ts
                number_of_votes = number_of_votes + 1

    if first_vote:
        os.remove(file_to_read)
        newvalues = {"log_processado": 1}
        filter = {"_id": urna['_id']}
        updateOne(db_conn, 'zonas_eleitorais', filter, newvalues)
        print("Sucesso: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ \
            str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']) +"; Numero de votos: " + str(number_of_votes))
        logger.info('Processamento de Boletim concluido.')
    else:
        print("Falha: UF: " + str(urna['SG_UF']) + "; MUN: "+ str(urna['CD_MUNICIPIO']) + "; ZONA: "+ \
            str(urna['NR_ZONA']) +"; SEC: "+  str(urna['NR_SECAO']))
        logger.error('Processamento de Boletim abortado.')



def unzipfile(filename):

    """
    1 - Obtem o campo 'file_name' dos documentos na collection zonas_eleitorais;
        Ex: '/database/boletins/PB-9/LogDeUrna_o00407-1905400090050_1668688124389.zip'
    2 - Averigua se file_name termina com .zip, e contem '/'
    3 - Quebra em duas variaveis: Dirname e Filename
    4 - Revisa a function unzipfile, ela precisa:
    a) receber o dirname e filename
    b) extrair localmente o zip ou logjez
    c) sempre retornar o nome do arquivo
    d) deletar o zip extraido

    """
    tmpFileLocation = config.get('default','temporaryDigestor')
    out = None

    if not os.path.isdir(tmpFileLocation):
        os.mkdir(tmpFileLocation)

    if filename and isinstance(filename, str):
        if '/' in filename and (filename.endswith('.zip') or filename.endswith('.logjez')): 
            filename_list = filename.split("/")
            file = filename_list[-1] 
            directory = '/'.join(filename_list[0:-1])

            # Extracting
            fullpath = os.path.abspath(filename) # get full path of files
            if filename.endswith('.zip'):
                try:
                    zip_ref = zipfile.ZipFile(fullpath, 'r') # create zipfile object
                    zip_ref.extractall(tmpFileLocation) # extract file to temp location
                    zip_ref.close() 
                except Exception as e:
                    logger.error('Falha ao abrir o boletim de urna ' + filename)
                    # Atualizando o documento na collection zonas_eleitorais para que seja baixado novamente
                    unsetOne(db_conn, 'zonas_eleitorais', {"file_name": filename}, {"file_name": "", "log_obtido": "" })
                    return None

            if filename.endswith('.logjez') or filename.endswith('.jez'):
                try:
                    zip_ref = Archive(fullpath)
                    zip_ref.extractall(tmpFileLocation) 
                except Exception as e:
                    logger.error('Falha ao abrir o boletim de urna ' + filename)
                    # Atualizando o documento na collection zonas_eleitorais para que seja baixado novamente
                    unsetOne(db_conn, 'zonas_eleitorais', {"file_name": filename}, {"file_name": "", "log_obtido": "" })
                    return None
            
            # retornando nome do arquivo:
            result_file = os.listdir(tmpFileLocation)
            result_file = result_file[0]

            if os.path.isfile(tmpFileLocation+'/'+result_file):
                if os.path.exists(directory + '/' + result_file):
                    os.remove(directory+ '/' + result_file)
                shutil.move(tmpFileLocation+'/'+result_file, directory)
                os.remove(fullpath) # delete zipped file
                out = directory + '/' + result_file

    return(out)


# Obtendo lista de dicionarios de todas urnas do estado:
filter = {'log_obtido': 1, 'log_processado': {'$exists': False}}
urnas = find(db_conn, 'zonas_eleitorais', filter)

for urna in urnas:
    zip_file_name = urna['file_name']
    lgjfile = unzipfile(zip_file_name)
    log = unzipfile(lgjfile)

    if log:
        logger.info('Arquivo descomprimido sendo processado: ' + log)
        digestFile(urna=urna, file_to_read=log, db_conn=db_conn)

exit(0)