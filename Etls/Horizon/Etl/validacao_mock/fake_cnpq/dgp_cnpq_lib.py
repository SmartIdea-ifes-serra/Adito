"""Substituto local do ``dgp_cnpq_lib`` para a validação com dados mock.

O ``CnpqCrawlerAdapter`` real do Horizon continua sendo usado (normalização da
URL, extração de membros, líderes e linhas); só a leitura do espelho no site do
CNPq é trocada pela leitura de ``cnpq_espelhos/*.json``. Um espelho com a chave
``__erro__`` simula falha de rede.
"""

import glob
import json
import os

PASTA_ESPELHOS = os.environ.get("HORIZON_MOCK_CNPQ", "dados/cnpq_espelhos")


class CnpqCrawler:
    def __init__(self):
        self._espelhos = {}
        for caminho in glob.glob(os.path.join(PASTA_ESPELHOS, "*.json")):
            with open(caminho, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
            self._espelhos[conteudo["url"]] = conteudo["espelho"]

    def get_data(self, url):
        espelho = self._espelhos.get(url)
        if espelho is None:
            raise ConnectionError(f"espelho mock não encontrado para {url}")
        if "__erro__" in espelho:
            raise TimeoutError(espelho["__erro__"])
        return json.loads(json.dumps(espelho))
