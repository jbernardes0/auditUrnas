from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
import time

e = "e545"
uf = ""
mubu = ""
zn = 
se = 

servico = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=servico)

page = 'https://resultados.tse.jus.br/oficial/app/index.html#/eleicao;e=e545;uf=ac;ufbu=ac;mubu=01120;zn=0008;se=0072/dados-de-urna/log-da-urna'
xpath = '/html/body/app-root/ion-app/ion-router-outlet/ng-component/div/div[2]/ng-component/app-dados-de-urna/app-log-da-urna/app-centralizar/div[2]/div[2]/div'

driver.get(page); time.sleep(3);
driver.refresh(); time.sleep(1);

driver.find_element('xpath', xpath).click(); time.sleep(1);

driver.close()