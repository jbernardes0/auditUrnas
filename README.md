# auditUrnas

"""
Auditoria de dados publicos do TSE
"""

"""
Objetivos:

 1 - Obter lista de zonas, seções e nr local votação (mubu - municipio??) por estado;
 2 - Iterar em todas as urls compostas pelas zonas e seções para baixar cada um dos logs de urna
     Exemplo de link composto de zona e seção 
     https://resultados.tse.jus.br/oficial/app/index.html#/eleicao;e=e545;uf=ac;ufbu=ac;mubu=01120;zn=0008;se=0072/dados-de-urna/log-da-urna

 3 - Processar todos os logs extraindo informações relevantes. Enviar problemas de processamento para um arquivo de log a parte. Carregar dados processados como documentos em um mongodb;
 4 - Iterar no documento, criando um campo de duração de votação (ordena os resultados por urna e timestamp, e adiciona um campo duração considerando o timestamp do anterior - timestamp do atual)

 5 - Com a base carregada e funcional, processar os seguintes dados:
    * Reportar votos com duração de operação inferior a meio minuto.
    * Reportar top 100 votos mais rápidos do Brasil.
    * gráfico de dispersão de votos no tempo (eixo X) considerando estado, região, municipio (eixo y).
    * mesmo anterior, filtrando modelo da urna (Avaliar como descobrir se é modelo novo ou não)
    * Como avaliar discrepancias fortes entre filtros regionais de maneira autonoma?

"""
