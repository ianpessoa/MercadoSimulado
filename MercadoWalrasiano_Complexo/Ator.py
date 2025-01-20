import random
import numpy as np
from dateutil.rrule import weekday
from scipy.optimize import minimize


class Ator:
    def __init__(self, id, dinheiro, bens_consumo, bens_producao, bens, tipo_bens, bens_necessario_producao, precos):
         self.id = id
         self.dinheiro = dinheiro

         self.precos = precos
         self.bens_consumo = bens_consumo
         self.bens_producao = bens_producao
         self.bens = bens
         self.tipo_bens = tipo_bens
         self.bens_necessario_producao = bens_necessario_producao

         #Expoentes da função utilidade
         self.definir_expoentes()

         self.bens_producao = bens_producao
         self.definir_trabalho_necessario()

         self.estoques = [0 for bem in self.bens_producao]

         self.ofertas = [0 for bem in self.bens]  # Estoque inicial de bens
         self.demandas = [0 for bem in self.bens]  # Estoque inicial de bens

         # Preferencia do agente (determina o indice de comparação entre utilidade presente e futura)
         self.preferencia_temporal = random.uniform(1,2)

    '''
    -- TEORIA DO CONSUMIDOR --
    '''

    def calcular_ganho_utilidade(self, ganho_futuro):
        """
        Calcula o ganho de utilidade que um ganho de dinheiro adicional no futuro propiciaria,
        com base nos preços correntes e na função de utilidade do agente.

        :param ganho_futuro: Quantidade adicional de renda a ser considerada
        :return: O ganho de utilidade proporcionado pelo ganho de dinheiro futuro
        """
        # Utilidade com a renda atual
        num_bens = len(self.bens_consumo)
        restricoes_atual = {'type': 'eq', 'fun': self.restricao_orcamentaria, 'args': (self.precos, self.dinheiro)}
        ponto_inicial_atual = [self.dinheiro * exp / sum(self.utilidade_expoentes) for exp in self.utilidade_expoentes]

        # Corrige o tamanho de bounds para coincidir com o número de bens
        bounds = [(0, None) for _ in range(num_bens)]

        resultado_atual = minimize(lambda x: -self.funcao_utilidade_consumo(x, self.utilidade_expoentes),
                                   ponto_inicial_atual,
                                   constraints=restricoes_atual,
                                   bounds=bounds,
                                   method='trust-constr')

        if not resultado_atual.success:
            #raise Exception("A otimização para calcular a utilidade atual falhou.")
            return 0

        utilidade_atual = -resultado_atual.fun

        # Utilidade com a renda futura
        renda_futura = self.dinheiro + ganho_futuro
        restricoes_futuro = {'type': 'ineq', 'fun': self.restricao_orcamentaria,
                             'args': (self.precos, renda_futura + 0.01)}
        ponto_inicial_futuro = [renda_futura * exp / sum(self.utilidade_expoentes) for exp in self.utilidade_expoentes]

        resultado_futuro = minimize(lambda x: -self.funcao_utilidade_consumo(x, self.utilidade_expoentes),
                                    ponto_inicial_futuro,
                                    constraints=restricoes_futuro,
                                    bounds=bounds,
                                    method='trust-constr')

        if not resultado_futuro.success:
            #raise Exception("A otimização para calcular a utilidade futura falhou.")
            return 0

        utilidade_futura = -resultado_futuro.fun
        ganho_utilidade = utilidade_futura - utilidade_atual

        return ganho_utilidade


    #Definir os expoentes da função utilidade
    def definir_expoentes(self):
        # Definindo a quantidade de bens de consumo
        n_bens = len(self.bens_consumo)

        # Gerando expoentes aleatórios
        expoentes_aleatorios = [random.uniform(0, 1) for _ in range(n_bens)]

        # Normalizando os expoentes para que a soma seja igual a 1
        soma_expoentes = sum(expoentes_aleatorios)
        self.utilidade_expoentes = [n_bens* expoente / soma_expoentes for expoente in expoentes_aleatorios]

    #Calcular a utilidade total de um consumo de bens
    def funcao_utilidade_consumo(self, qtds, expoentes):
        """Calcula a utilidade com base nas quantidades consumidas e expoentes."""
        utilidade = 0
        for i in range(len(self.bens)):
            if self.tipo_bens[i] == 0:
                utilidade *= np.clip(qtds[i], 1e-10, None) ** expoentes[i]
            else:
                utilidade += 0
        if np.isnan(utilidade) or np.isinf(utilidade):
            raise ValueError("Função utilidade contém valores inválidos (NaN ou infinito).")
        return utilidade

    # Calcular a utilidade total de um consumo/produção de bens
    def funcao_utilidade_geral(self, qtds, expoentes):
        """Calcula a utilidade com base nas quantidades consumidas e expoentes."""
        utilidade = 0
        for i in range(len(self.bens)):
            if self.tipo_bens[i] == 0:
                utilidade *= qtds[i] ** expoentes[i]
            else:
                renda_extra = self.encontra_melhor_produto(i,qtds[i])-(qtds[i]*self.precos[i])
                if renda_extra > 0:
                    utilidade += self.calcular_ganho_utilidade(renda_extra)
        return utilidade

    #Calcular a restrição orçamentária para um determinado nivel de renda e preços
    def restricao_orcamentaria(self,consumo, precos, renda):
        """Calcula a diferença entre o gasto e a renda."""
        return renda - sum(preco * quantidade for preco, quantidade in zip(precos, consumo))

    #Calcular a quantidade de demanda do agente que otimizaria sua utilidade para uma dada renda e preços
    def calcular_demanda(self):
        # Ponto inicial para as quantidades consumidas
        consumo_inicial = [self.dinheiro / sum(self.precos)] * len(self.precos)  # Divida a renda igualmente

        # Restrições
        restricoes = {'type': 'eq', 'fun': self.restricao_orcamentaria, 'args': (self.precos, self.dinheiro)}

        # Limites: as quantidades devem ser não-negativas
        limites = [(0, None) for _ in self.precos]

        # Função de otimização
        resultado = minimize(lambda x: -self.funcao_utilidade_geral(x, self.utilidade_expoentes),  # Maximizar a utilidade
                             consumo_inicial,  # Ponto inicial
                             constraints=restricoes,  # Restrições orçamentárias
                             bounds=limites)  # Limites das quantidades

        if resultado.success:
            self.demandas = resultado.x
            return resultado.x  # Retorna as quantidades que maximizam a utilidade
        else:
            #raise Exception("A otimização falhou.")
            self.demandas = [0 for bem in self.bens]
            return self.demandas

    '''
    -- TEORIA DO PRODUTOR --
    '''
    # Definir os expoentes da função utilidade
    def definir_trabalho_necessario(self):
        # Definindo a quantidade de bens de consumo
        n_bens = len(self.bens)

        # Gerando expoentes aleatórios
        expoentes_aleatorios = [random.uniform(1, 2) for _ in range(n_bens)]

        # Normalizando os expoentes para que a soma seja igual a 1
        soma_expoentes = sum(expoentes_aleatorios)
        self.trabalho_necessario = [n_bens * expoente / soma_expoentes for expoente in expoentes_aleatorios]

    #O objetivo dessa função é encontrar o melhor bem a ser produzido pelo bem de produção
    #passado como parametro e a sua respectiva receita
    def encontra_melhor_produto(self,indice_bem,qtd):
        receitas = []
        indice_bem -= len(self.bens_consumo)
        for i in range(len(self.bens_necessario_producao)):
            if self.bens_necessario_producao[i][indice_bem] > 0:
                parte = (self.bens_necessario_producao[i][indice_bem])/sum(self.bens_necessario_producao[i])
                receitas.append((self.precos[i]*parte*qtd)/self.preferencia_temporal) #A receita "potencial" será a produtividade marginal do bem de produção
            else:
                receitas.append(0)
        return max(receitas)

    def receita_total(self,qtd_bens, precos):
        """Função objetivo: receita total em função das quantidades de bens."""
        receitas = [0 for i in range(len(qtd_bens))]
        for i in range(len(qtd_bens)):
            if self.tipo_bens[i] == 1:
                maior_receita = self.encontra_melhor_produto(i, qtd_bens[i])
                if maior_receita > qtd_bens[i] * precos[i]:
                    receitas[i] = maior_receita #Se a receita de vender um bem de consumo produzido for maior
                else:
                    receitas[i] = qtd_bens[i] * precos[i] #Se a receita de vender o proprio bem de produção for maior
            else:
                receitas[i] = qtd_bens[i] * precos[i]
        return -np.dot(precos, qtd_bens)  # Negativo porque estamos minimizando (maximize ao minimizar o negativo)

    def restricao_trabalho(self,qtd_bens, trabalho_necessario, trabalho_disponivel, alpha):
        """Função de restrição: trabalho total necessário para produzir os bens."""
        trabalho_total = sum(trabalho_necessario[i] * (qtd_bens[i] ** alpha) for i in range(len(qtd_bens)))
        return trabalho_disponivel - trabalho_total

    def restricao_producao(self, qtd_bens, bens_necessario_producao, estoque):
        """
        Restringe as quantidades de bens de consumo com base no estoque disponível de bens de produção.
        """
        restricoes = []
        estoque = estoque.copy()
        estoque_necessario = [0 for e in estoque]

        for i in range(len(self.bens_consumo)):
            for j in range(len(self.bens_producao)):
                estoque_necessario[j] += self.bens_necessario_producao[i][j] * qtd_bens[i]

        for i in range(len(self.bens_producao)):
            restricoes.append(estoque[i] - estoque_necessario[i])

        return np.array(restricoes)

    def reduzir_estoques(self,indice_bem,qtd):
        for i in range(len(self.bens_necessario_producao[indice_bem])):
            self.estoques[i] -= qtd*self.bens_necessario_producao[indice_bem][i]

    def maximizar_receita(self, trabalho_disponivel, controle, alpha=1.5, beta=0.05):
        """Encontra a alocação de trabalho que maximiza a receita, dado o trabalho disponível."""

        # Número de bens
        n = len(self.precos)

        # Incremento da produtividade coletiva ajustado antes da otimização
        trabalho_necessario_ajustado = [
            self.trabalho_necessario[i] / (1 + beta * controle.qtd_trabalho[i]) for i in range(n)
        ]

        # Estimativa inicial de quantidades (palpite inicial para otimização)
        qtd_inicial = np.ones(n)

        # Definindo as restrições de trabalho e produção
        restricao_trabalho= {'type': 'ineq', 'fun': self.restricao_trabalho,
                     'args': (trabalho_necessario_ajustado, trabalho_disponivel, alpha)}

        restricao_producao = {'type': 'ineq', 'fun': self.restricao_producao,
                              'args': (self.bens_necessario_producao, self.estoques)}

        bounds = []
        for i in range(len(self.bens)):
            if self.tipo_bens[i] == 0:
                qtd_max = 0
                razoes = []
                for j in range(len(self.bens_necessario_producao[i])):
                    if self.estoques[j] > 0 and self.bens_necessario_producao[i][j] > 0:
                        razoes.append(self.estoques[j]/self.bens_necessario_producao[i][j])
                    if self.estoques[j] <= 0:
                        qtd_max = 0
                bounds.append((0,None))
            else:
                bounds.append((0,None))

        # Rodando a otimização
        resultado = minimize(self.receita_total, qtd_inicial, args=(self.precos,),
                             constraints=[restricao_trabalho, restricao_producao], method='SLSQP', bounds=bounds)

        # Retorna as quantidades ótimas e a receita total correspondente
        qtd_otima = resultado.x

        for i in range(len(resultado.x)):
            controle.qtd_produzida += qtd_otima[i]
            if self.tipo_bens[i] == 0:
                # Se for bem de consumo, decidir entre consumir ou ofertar
                if self.demandas[i] > qtd_otima[i]:
                    self.demandas[i] -= qtd_otima[i]
                else:
                    qtd_otima[i] -= self.demandas[i]
                    self.demandas[i] = 0
                    self.ofertas[i] = qtd_otima[i]
                self.reduzir_estoques(i, qtd_otima[i])
            else:
                #Se for bem de produção, avaliar se é melhor ofertar ou estocar
                if self.encontra_melhor_produto(i, qtd_otima[i]) > self.precos[i] * qtd_otima[i]:
                    self.estoques[i - len(self.bens_consumo)] += qtd_otima[i]
                else:
                    self.ofertas[i] += qtd_otima[i]
                #Se o bem de produção estava sendo demandado pelo agente
                if self.demandas[i] > qtd_otima[i]:
                    self.demandas[i] -= qtd_otima[i]
                else:
                    qtd_otima[i] -= self.demandas[i]
                    self.demandas[i] = 0
        receita_max = -resultado.fun  # Recupera o valor da receita máxima

        # Calcula o trabalho utilizado para produzir cada bem e atualiza o controle com base no ajustado
        trabalho_medio = trabalho_disponivel / n
        for i in range(n):
            trabalho_usado = trabalho_necessario_ajustado[i] * (qtd_otima[i] ** alpha)
            if self.tipo_bens[i] == 0:
                # Adicionando o trabalho necessário para produzir os bens de produção utilizados na produção do bem de consumo
                for j in range(len(self.bens_necessario_producao[i])):
                    if controle.valores[j + len(self.bens_consumo)] > 0:
                        trabalho_usado += self.bens_necessario_producao[i][j] * qtd_otima[i] * controle.valores[
                            j + len(self.bens_consumo)]
                    else:
                        '''Se o bem de produção ainda não tiver valor definido
                        trabalho_necessario_ajustado[len(self.bens_consumo)+j]: Quantidade de trabalho necessario para produzir
                         a unidade do bem de produção
                         self.bens_necessario_producao[i][j]: Quantidade do bem de produção que precisa ser produzido para a produção de 1 bem
                         '''
                        trabalho_usado += trabalho_necessario_ajustado[len(self.bens_consumo) + j] * \
                                          self.bens_necessario_producao[i][j] * (qtd_otima[i] ** alpha)

            controle.qtd_trabalho[i] += trabalho_usado

            # Atualiza o trabalho necessário para o próximo cálculo, se estiver acima de um limite e com uso alto
            if self.trabalho_necessario[i] >= 1.0 and trabalho_usado > trabalho_medio:
                self.trabalho_necessario[i] /= random.uniform(1, 1.015)
        self.ajustar_estoques_e_ofertas()
        return receita_max

    def ajustar_estoques_e_ofertas(self):
        for i in range(len(self.estoques)):
            if self.estoques[i] > 0 and self.encontra_melhor_produto(i+len(self.bens_consumo),self.estoques[i]) < self.estoques[i] * self.precos[i+len(self.bens_consumo)]:
                self.ofertas[i+len(self.bens_consumo)] += self.estoques[i]
                self.estoques[i] = 0
