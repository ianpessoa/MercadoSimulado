import random
import numpy as np
from dateutil.rrule import weekday
from scipy.optimize import minimize


class Ator:
    def __init__(self, id, dinheiro, bens_consumo, precos_bens_consumo):
         self.id = id
         self.dinheiro = dinheiro

         self.bens_consumo = bens_consumo
         self.precos_bens_consumo = precos_bens_consumo


         #Expoentes da função utilidade
         self.definir_expoentes()

         self.bens_producao = []
         self.definir_trabalho_necessario()

         self.ofertas = [0 for bem in self.bens_consumo]  # Estoque inicial de bens
         self.demandas = [0 for bem in self.bens_consumo]  # Estoque inicial de bens

         self.elasticidade_oferta = random.uniform(1,2)
    '''
    -- TEORIA DO CONSUMIDOR --
    '''
    #Definir os expoentes da função utilidade
    def definir_expoentes(self):
        # Definindo a quantidade de bens de consumo
        n_bens = len(self.bens_consumo)

        # Gerando expoentes aleatórios
        expoentes_aleatorios = [random.uniform(0, 5) for _ in range(n_bens)]

        # Normalizando os expoentes para que a soma seja igual a 1
        soma_expoentes = sum(expoentes_aleatorios)
        self.utilidade_expoentes = [n_bens* expoente / soma_expoentes for expoente in expoentes_aleatorios]

    #Calcular a utilidade total de um consumo de bens
    def funcao_utilidade(self,consumo, expoentes):
        """Calcula a utilidade com base nas quantidades consumidas e expoentes."""
        return np.prod([quantidade ** expoente for quantidade, expoente in zip(consumo, expoentes)])

    #Calcular a restrição orçamentária para um determinado nivel de renda e preços
    def restricao_orcamentaria(self,consumo, precos, renda):
        """Calcula a diferença entre o gasto e a renda."""
        return renda - sum(preco * quantidade for preco, quantidade in zip(precos, consumo))

    #Calcular a quantidade de demanda do agente que otimizaria sua utilidade para uma dada renda e preços
    def calcular_demanda(self):
        # Ponto inicial para as quantidades consumidas
        consumo_inicial = [self.dinheiro / sum(self.precos_bens_consumo)] * len(self.precos_bens_consumo)  # Divida a renda igualmente

        # Restrições
        restricoes = {'type': 'eq', 'fun': self.restricao_orcamentaria, 'args': (self.precos_bens_consumo, self.dinheiro)}

        # Limites: as quantidades devem ser não-negativas
        limites = [(0, None) for _ in self.precos_bens_consumo]

        # Função de otimização
        resultado = minimize(lambda x: -self.funcao_utilidade(x, self.utilidade_expoentes),  # Maximizar a utilidade
                             consumo_inicial,  # Ponto inicial
                             constraints=restricoes,  # Restrições orçamentárias
                             bounds=limites)  # Limites das quantidades

        if resultado.success:
            self.demandas = resultado.x
            return resultado.x  # Retorna as quantidades que maximizam a utilidade
        else:
            #raise Exception("A otimização falhou.")
            self.demandas = [0 for bem in self.bens_consumo]
            return self.demandas

    '''
    -- TEORIA DO PRODUTOR --
    '''

    # Definir os expoentes da função utilidade
    def definir_trabalho_necessario(self):
        # Definindo a quantidade de bens de consumo
        n_bens = len(self.bens_consumo)

        # Gerando expoentes aleatórios
        expoentes_aleatorios = [random.uniform(1, 4) for _ in range(n_bens)]

        # Normalizando os expoentes para que a soma seja igual a 1
        soma_expoentes = sum(expoentes_aleatorios)
        self.trabalho_necessario = [n_bens * expoente / soma_expoentes for expoente in expoentes_aleatorios]

    def receita_total(self,qtd_bens, precos):
        """Função objetivo: receita total em função das quantidades de bens."""
        return -np.dot(precos, qtd_bens)  # Negativo porque estamos minimizando (maximize ao minimizar o negativo)

    def restricao_trabalho(self,qtd_bens, trabalho_necessario, trabalho_disponivel, alpha):
        """Função de restrição: trabalho total necessário para produzir os bens."""
        trabalho_total = sum(trabalho_necessario[i] * (qtd_bens[i] ** alpha) for i in range(len(qtd_bens)))
        return trabalho_disponivel - trabalho_total

    def maximizar_receita(self, trabalho_disponivel, controle, alpha=1.5, beta=0.01):
        """Encontra a alocação de trabalho que maximiza a receita, dado o trabalho disponível."""

        # Número de bens
        n = len(self.precos_bens_consumo)

        # Incremento da produtividade coletiva ajustado antes da otimização
        trabalho_total = sum(controle.qtd_trabalho)
        if trabalho_total > 0:
            trabalho_necessario_ajustado = [
                self.trabalho_necessario[i] / (1 + beta * controle.qtd_trabalho[i]/trabalho_total) for i in range(n)
            ]
        else:
            trabalho_necessario_ajustado = self.trabalho_necessario
        # Estimativa inicial de quantidades (palpite inicial para otimização)
        qtd_inicial = np.ones(n)

        # Definindo a restrição de trabalho total com base no trabalho ajustado
        restricao = {'type': 'ineq', 'fun': self.restricao_trabalho,
                     'args': (trabalho_necessario_ajustado, trabalho_disponivel, alpha)}

        # Rodando a otimização
        resultado = minimize(self.receita_total, qtd_inicial, args=(self.precos_bens_consumo,),
                             constraints=[restricao], method='SLSQP', bounds=[(0, None)] * n)

        # Retorna as quantidades ótimas e a receita total correspondente
        qtd_otima = resultado.x
        self.ofertas = qtd_otima
        receita_max = -resultado.fun  # Recupera o valor da receita máxima

        # Calcula o trabalho utilizado para produzir cada bem e atualiza o controle com base no ajustado
        trabalho_medio = trabalho_disponivel / n
        for i in range(n):
            trabalho_usado = trabalho_necessario_ajustado[i] * (qtd_otima[i] ** alpha)
            controle.qtd_trabalho[i] += trabalho_usado

            # Atualiza o trabalho necessário para o próximo cálculo, se estiver acima de um limite e com uso alto
            if self.trabalho_necessario[i] >= 1.0 and trabalho_usado > trabalho_medio:
                self.trabalho_necessario[i] /= random.uniform(1, 1.015)

        return receita_max