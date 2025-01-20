class Controle():
    def __init__(self,bens):
        self.historico_precos = []
        self.historico_demandas = []
        self.historico_ofertas = []

        self.qtd_trabalho = [0 for bem in bens]
        self.qtd_produzida = [0 for ben in bens]
        self.qtd_estoques = [0 for bem in bens]
        self.qtd_ofertas = [0 for bem in bens]
        self.qtd_trabalho_trocada = 0.0
        self.valores = [0 for bem in bens]
        self.historico_valores = []

        self.qtd_dinheiro_rodado = 0.0
        self.historico_dinheiro_rodado = []
        self.historico_dinheiro = []

        self.historico_oferta_agregada = []
        self.historico_demanda_agregada = []

        self.historico_valor_realizado_agregado = []
        self.historico_oferta_valor_agregado = []
        self.historico_demanda_valor_agregado = []

    def atualiza_estoques_e_ofertas(self,agentes):
        for agente in agentes:
            for i in range(len(agente.estoques)):
                self.qtd_estoques[len(agente.bens_consumo)+i] += agente.estoques[i]
            for i in range(len(agente.ofertas)):
                self.qtd_ofertas[i] += agente.ofertas[i]


    def calcular_qtd_trabalho_trocada(self,ofertas,demandas,excesso_demanda):
        for i in range(len(ofertas)):
            if (excesso_demanda[i] >= 0):
                self.qtd_trabalho_trocada += self.qtd_trabalho[i]
            else:
                self.qtd_trabalho_trocada += (self.qtd_trabalho[i]*demandas[i])/self.qtd_produzida[i]

    def calcular_valores(self,rodada):
        for i in range(len(self.qtd_produzida)):
            if self.qtd_trabalho[i] != 0:
                self.valores[i] = self.qtd_trabalho[i]/self.qtd_produzida[i] * self.qtd_dinheiro_rodado/self.qtd_trabalho_trocada
            else:
                if len(self.historico_valores) > 0:
                    self.valores[i] = self.historico_valores[rodada-1][i]
                else:
                    self.valores[i] = self.historico_precos[0][i]

    def calcular_valor_agregado(self,ofertas,demandas,excesso_demanda,rodada):
        for i in range(len(ofertas)):
            self.historico_oferta_valor_agregado[rodada] += ofertas[i]*self.valores[i]
            self.historico_demanda_valor_agregado[rodada] += demandas[i] * self.valores[i]
            if (excesso_demanda[i] >= 0):
                self.historico_valor_realizado_agregado[rodada] += ofertas[i]*self.valores[i]
            else:
                self.historico_valor_realizado_agregado[rodada] += demandas[i]*self.valores[i]