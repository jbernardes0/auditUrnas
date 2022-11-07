from base64 import encode
from genericpath import isfile
import pprint
import csv
import os

from mongo_methods import insertMany, insertOne, mongodb_conn

"""
Debug - Uso do pretty print para json:
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(dict)
"""

# Funcao de processamento de CSV, e alimentacao da collection zonas_eleitorais
def digest_csv(csv_name):
    if csv_name.endswith('.csv'):
        # Atributos carregados dos arquivos CSV:
        desired_attributes = ['CD_ELEICAO', 'SG_UF', 'CD_MUNICIPIO', 'NR_ZONA', 'NR_SECAO']

        # Lista contendo resultados de apuração por estado
        result = []

        with open(csv_name, mode="r", encoding="latin-1") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                row_consolid = { x: row[x] for x in desired_attributes}
                result.append(row_consolid)
            
        # Uma vez que os resultados no csv de origem havia 4 rows para cada urna, para consolidar votos PL, PT, nulos e Brancos,
        # ao selecionar apenas os campos definidos em 'desired_attributes' se faz necessario remover duplicadas do dict:
        res_wo_dupl = [i for n, i in enumerate(result) if i not in result[n + 1:]]
        result = res_wo_dupl

        # Persistindo resultados numa collection, instancia mongo deployada localmente
        mongo_conn = mongodb_conn('mongodb://localhost:27017/')
        db_conn = mongo_conn["audit_eleicao_2022"]
        coll = "zonas_eleitorais"

        insertMany(db_conn, coll, result)
        print("- UF {}: {} registros inseridos!".format(result[0]['SG_UF'],len(result)))

csv_dir = '/home/jobernardes/Documents/Projects/personal_auditLogs/database/boletins/'

for filename in os.listdir(csv_dir):
    f = os.path.join(csv_dir, filename)
    if os.path.isfile(f):
        digest_csv(f)

# EOF