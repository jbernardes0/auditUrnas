import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from configparser import ConfigParser

from pprint import pprint
import os

from mongo_methods import mongodb_conn, find

# Cfgparse
config = ConfigParser()
config.read('auditBu.cfg')

# Mongodb Connection
mongo_conn = mongodb_conn(config.get('default','mongoString'))
db_conn = mongo_conn[config.get('default','mongoDbName')]

reportLocation = config.get('default','temporaryReport')
# Matplotlib default report location
if not os.path.isdir(reportLocation):
    os.mkdir(reportLocation)

mpl.rcParams["savefig.directory"] = reportLocation

filters = {"secs_elaps": {"$gte": 0, "$lt": 22}}
urnas = find(db_conn, 'resultados_de_urna', filters)

pprint(urnas)

df = pd.DataFrame.from_records(urnas)
unid_fed = df['SG_UF']
secs_elaps = df['secs_elaps']

plt.bar(unid_fed,secs_elaps)
plt.xlabel("teste1")
plt.xlabel("teste2")