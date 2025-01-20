import random
import numpy as np

import matplotlib.pyplot as plt

from Ator import Ator
from Controle import Controle

class LeiloeiroWalrasiano:
    def __init__(self, bens, dinheiro_total,qtd_bens,qtd_agentes):
        self.precos = [random.uniform(0, dinheiro_total/(qtd_agentes)) for bem in bens]
        self.dinheiro_total = dinheiro_total

    def reajustar_precos(self, excesso_demanda):
        for i in range(len(excesso_demanda)):
            excesso = excesso_demanda[i]

            # Definindo uma base que controla a taxa de ajuste; quanto maior a base, menor a sensibilidade
            base = 1.005

            # Atribuindo um fator que cresce com o aumento do excesso, mas é suavizado pela base
            fator = base ** abs(excesso)

            # Limitando o fator para um intervalo razoável
            fator = min(fator, 1.5)

            # Choque estocastico
            fator = random.uniform(1,fator)

            if abs(excesso) < 0.0005:
                fator = 1

            # Ajuste proporcional do preço
            if excesso > 0:
                self.precos[i] *= fator
            elif excesso < 0:
                self.precos[i] /= fator

    def imprimir_precos(self):
        print("Preços atuais das mercadorias:", self.precos)


class Mercado:
    def __init__(self, num_agentes, num_dinheiro, num_mercadorias):
        self.num_dinheiro = num_dinheiro * num_agentes
        self.num_bens_producao = 0 #(num_mercadorias + 2) // 3
        self.num_bens_consumo = num_mercadorias - self.num_bens_producao
        self.bens_consumo = [f'Consumo_{i}' for i in range(self.num_bens_consumo)]
        self.bens_producao = [] #[f'Producao_{i}' for i in range(self.num_bens_producao)]
        self.leiloeiro = LeiloeiroWalrasiano(self.bens_consumo, self.num_dinheiro,self.num_bens_consumo,num_agentes)
        self.qtd_agentes = num_agentes
        self.agentes = [Ator(i, num_dinheiro, self.bens_consumo, self.leiloeiro.precos) for i in range(num_agentes)]

        self.excesso_demanda = [0 for bem in self.bens_consumo]
        self.trocas = []  # Registro de trocas realizadas


        self.demanda_total = [0 for bem in self.bens_consumo]
        self.oferta_total = [0 for bem in self.bens_consumo]
        self.qtd_agentes_ofertas = []
        self.qtd_agentes_demandas = []

        self.controle = Controle(self.bens_consumo)
        self.receita_max = 0.0


    def calcular_excesso_demanda(self):
        # Cálculo do excesso de demanda baseado na demanda e oferta reais
        for i in range(len(self.excesso_demanda)):
            self.excesso_demanda[i] = self.demanda_total[i] - self.oferta_total[i]

    def contar_agentes_ofertas_positivas(self,ofertas):
        """Conta quantos agentes têm uma oferta positiva para cada bem."""
        # Inicializa uma lista para contar ofertas positivas
        contador_ofertas = [0] * len(ofertas[0])  # Cria uma lista de zeros com o tamanho da primeira lista

        # Itera por cada agente nas ofertas
        for oferta in ofertas:
            for i, quantidade in enumerate(oferta):
                if quantidade > 0:
                    contador_ofertas[i] += 1  # Incrementa o contador para o índice correspondente

        return contador_ofertas

    def rodar_rodada(self,qtd_trabalho):
        demandas_agentes = []
        ofertas_agentes = []
        for agente in self.agentes:
            agente.calcular_demanda()
            demandas_agentes.append(agente.demandas)
            self.receita_max += agente.maximizar_receita(qtd_trabalho,self.controle)
            ofertas_agentes.append(agente.ofertas)
        self.demanda_total = [sum(elementos) for elementos in zip(*demandas_agentes)]
        self.oferta_total = [sum(elementos) for elementos in zip(*ofertas_agentes)]
        self.calcular_excesso_demanda()

        self.qtd_agentes_ofertas = self.contar_agentes_ofertas_positivas(ofertas_agentes)
        self.qtd_agentes_demandas = self.contar_agentes_ofertas_positivas(demandas_agentes)
        for agente in self.agentes:
            for i in range(len(agente.ofertas)):
                if agente.ofertas[i] > 0:
                    if self.excesso_demanda[i] >= 0:
                        agente.dinheiro += agente.ofertas[i] * agente.precos_bens_consumo[i]
                        self.controle.qtd_dinheiro_rodado += agente.ofertas[i] * agente.precos_bens_consumo[i]
                        #print(f"AGENTE {agente.id} vendeu {agente.ofertas[i]} de "
                       #       f"{agente.bens_consumo[i]}, "
                      #        f"receita de {agente.ofertas[i] * agente.precos_bens_consumo[i]}")
                    else:
                        agente.dinheiro += self.demanda_total[i]/self.qtd_agentes_ofertas[i] * agente.precos_bens_consumo[i]
                        self.controle.qtd_dinheiro_rodado += self.demanda_total[i]/self.qtd_agentes_ofertas[i] * agente.precos_bens_consumo[i]
                     #   print(f"AGENTE {agente.id} vendeu {self.demanda_total[i]/qtd_agentes_ofertas[i]} de "
                    #          f"{agente.bens_consumo[i]}, "
                   #           f"receita de {self.demanda_total[i]/qtd_agentes_ofertas[i] * agente.precos_bens_consumo[i]}")

            for j in range(len(agente.demandas)):
                if agente.demandas[j] > 0:
                    if self.excesso_demanda[j] <= 0:
                        agente.dinheiro -= agente.demandas[j] * agente.precos_bens_consumo[j]
                  #      print(f"AGENTE {agente.id} comprou {agente.demandas[j]} de "
                 #             f"{agente.bens_consumo[j]}, "
                #              f"custo de {agente.demandas[j] * agente.precos_bens_consumo[j]}")
                    else:
                        agente.dinheiro -= self.oferta_total[j]/self.qtd_agentes_demandas[j]*agente.precos_bens_consumo[j]
               #         print(f"AGENTE {agente.id} comprou {self.oferta_total[j] / qtd_agentes_demandas[j]} de "
              #                f"{agente.bens_consumo[j]}, "
             #                 f"custo de {self.oferta_total[j] / qtd_agentes_demandas[j] * agente.precos_bens_consumo[j]}")
            #print(f"DINHEIRO DO AGENTE {agente.id}: {agente.dinheiro}")



    def rodar(self, num_rodadas):
        qtd_trabalho = 1
        for rodada in range(num_rodadas):
            print(f"Rodada {rodada + 1}")
            self.rodar_rodada(qtd_trabalho)

            #Registrando valores
            self.controle.calcular_qtd_trabalho_trocada(self.oferta_total,self.demanda_total,self.excesso_demanda)
            self.controle.historico_precos.append(self.leiloeiro.precos.copy())
            self.controle.calcular_valores(self.oferta_total,rodada)
            #Registrando no historico
            self.controle.historico_demandas.append(self.demanda_total)
            self.controle.historico_ofertas.append(self.oferta_total)
            self.controle.historico_valores.append(self.controle.valores.copy())
            self.controle.historico_dinheiro_rodado.append(self.controle.qtd_dinheiro_rodado)
            self.controle.historico_dinheiro.append(self.num_dinheiro)
            #Registrando demanda e oferta agergada
            self.controle.historico_demanda_agregada.append(0.0)
            self.controle.historico_oferta_agregada.append(0.0)
            self.controle.historico_valor_realizado_agregado.append(0.0)
            self.controle.historico_oferta_valor_agregado.append(0.0)
            self.controle.historico_demanda_valor_agregado.append(0.0)
            self.controle.calcular_valor_agregado(self.oferta_total,self.demanda_total,self.excesso_demanda,rodada)
            for i in range(len(self.bens_consumo)):
                self.controle.historico_demanda_agregada[rodada] \
                    += self.demanda_total[i]*self.leiloeiro.precos[i]
                self.controle.historico_oferta_agregada[rodada] \
                    += self.oferta_total[i] * self.leiloeiro.precos[i]

            #Reajustando mercado
            self.leiloeiro.reajustar_precos(self.excesso_demanda)


            for agente in self.agentes:
                agente.precos_bens_consumo = self.leiloeiro.precos
            self.relatorio(rodada + 1)
            self.consumo_e_eliminacao(rodada + 1)

    def consumo_e_eliminacao(self, rodada):
        for agente in self.agentes:
            agente.ofertas = [0 for bem in self.bens_consumo]
            agente.demandas = [0 for bem in self.bens_consumo]
        self.controle.qtd_dinheiro_rodado = 0.0
        self.controle.qtd_trabalho = [0 for bem in self.bens_consumo]
        self.controle.qtd_trabalho_trocada = 0.0

    def relatorio(self, rodada):
        print(f"--- Relatório da rodada {rodada} ---")
        self.leiloeiro.imprimir_precos()
        print("Valores:",self.controle.valores)
        print("Soma dos valores:",self.controle.historico_oferta_valor_agregado[rodada-1])
        print("Soma dos preços:",self.controle.historico_oferta_agregada[rodada-1])
        print("Excesso de demanda:", self.excesso_demanda)
        print("Qtd Trabalho:",self.controle.qtd_trabalho)
        print("Ofertas:",self.oferta_total)
        print("Demandas:",self.demanda_total)
        if rodada % 700 == 0:
           self.gerar_graficos_oferta_demanda()
        if rodada % 2000 == 0:
            self.plotar_curva_lorenz(self.agentes)

    def gerar_graficos_oferta_demanda(self):
        num_rodadas = len(self.controle.historico_precos)
        rodadas = list(range(num_rodadas))  # Eixo x para o primeiro gráfico (rodadas)

        for i, bem in enumerate(self.bens_consumo):
            # Extrai os dados históricos de preços, valores, ofertas e demandas para o bem em questão
            ofertas = [self.controle.historico_ofertas[rodada][i] for rodada in rodadas]
            demandas = [self.controle.historico_demandas[rodada][i] for rodada in rodadas]
            precos = [self.controle.historico_precos[rodada][i] for rodada in rodadas]
            valores = [self.controle.historico_valores[rodada][i] for rodada in rodadas]

            # Gráfico 0: Dinheiro utilizado, oferta agregada e demanda agregada durante as rodadas
            plt.figure(figsize=(10, 5))
            plt.plot(rodadas, self.controle.historico_dinheiro_rodado, label='Dinheiro Utilizado', color='green')
            plt.plot(rodadas, self.controle.historico_dinheiro, label='Dinheiro Total', color='blue')
            plt.plot(rodadas,self.controle.historico_demanda_agregada, label='Demanda Agregada', color='red')
            plt.plot(rodadas, self.controle.historico_oferta_agregada, label='Oferta*Preço Agregada', color='yellow')
            plt.plot(rodadas,self.controle.historico_valor_realizado_agregado,label='Valor Realizado Agregado',color='Black')
            plt.plot(rodadas, self.controle.historico_oferta_valor_agregado, label='Oferta*Valor Agregada',
                     color='Pink')
            plt.plot(rodadas, self.controle.historico_demanda_valor_agregado, label='Demanda*Valor Agregada',
                     color='Purple')
            plt.title(f'Dinheiro utilizado e oferta e demanda agregadas durante as rodadas')
            plt.xlabel('Rodadas')
            plt.ylabel('Quantidade de Dinheiro')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Grafico 0.1: Diferença oferta agregada medida em preços e em valores:
            diferenca_oferta_agregada = [abs(self.controle.historico_oferta_agregada[j] - self.controle.historico_oferta_valor_agregado[j]) for j in rodadas]
            plt.figure(figsize=(10, 5))
            plt.plot(rodadas, diferenca_oferta_agregada, label='Erro (Valor Agregado - Preço agregado)', color='purple')
            plt.title(f'Aproximação de Valor agregado aos Preço agregado ao longo das rodadas')
            plt.xlabel('Rodadas')
            plt.ylabel('Erro Absoluto (|Valor - Preço|)')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Gráfico 0.2: Diferença entre oferta agregada em preços e valores comparada  com diferença entre oferta e demanda agredada

            diferenca_oferta_agregada = [
                abs(self.controle.historico_oferta_agregada[j] - self.controle.historico_oferta_valor_agregado[j]) for j
                in rodadas]
            diferenca_ofertatotal_demandatotal = [abs(self.controle.historico_oferta_agregada[j] - self.controle.historico_demanda_agregada[j]) for j
                in rodadas]
            plt.figure(figsize=(10, 5))
            plt.plot(diferenca_oferta_agregada, diferenca_ofertatotal_demandatotal, 'o-', color='orange',
                     label='Erro Agregado vs Oferta-Demanda Agregadas')
            plt.title(f'Aproximação dos Valores aos Preços (Agregados) conforme Oferta se aproxima de Demanda (Agregados)')
            plt.xlabel('Erro (|Oferta - Demanda|)')
            plt.ylabel('Erro Absoluto (|Valor - Preço|)')
            plt.legend()
            plt.grid(True)
            plt.show()


            # Gráfico 1: Preço, oferta e demanda ao longo das rodadas
            plt.figure(figsize=(10, 5))
            plt.plot(rodadas, ofertas, label='Oferta', color='green')
            plt.plot(rodadas, demandas, label='Demanda', color='red')
            plt.title(f'Variação de Preço, Oferta e Demanda para {bem} ao longo das rodadas')
            plt.xlabel('Rodadas')
            plt.ylabel('Quantidade/Preço')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Gráfico 2: Preço e valor ao longo das rodadas
            plt.figure(figsize=(10, 5))
            plt.plot(rodadas, precos, label='Preço', color='green')
            plt.plot(rodadas, valores, label='Valor', color='red')
            plt.title(f'Variação de Preço e Valor para {bem} ao longo das rodadas')
            plt.xlabel('Rodadas')
            plt.ylabel('Valor/Preço')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Gráfico 3: Preço em função da oferta e demanda
            plt.figure(figsize=(10, 5))
            plt.plot(ofertas, precos, 'o-', label='Oferta vs Preço', color='green')
            plt.plot(demandas, precos, 'o-', label='Demanda vs Preço', color='red')
            plt.title(f'Relação entre Preço, Oferta e Demanda para {bem}')
            plt.xlabel('Quantidade (Oferta/Demanda)')
            plt.ylabel('Preço/Valor')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Gráfico 4: Aproximação dos valores em relação aos preços
            diferenca_valores_precos = [abs(valores[j] - precos[j]) for j in rodadas]
            plt.figure(figsize=(10, 5))
            plt.plot(rodadas, diferenca_valores_precos, label='Erro (Valor - Preço)', color='purple')
            plt.title(f'Aproximação de Valores aos Preços para {bem} ao longo das rodadas')
            plt.xlabel('Rodadas')
            plt.ylabel('Erro Absoluto (|Valor - Preço|)')
            plt.legend()
            plt.grid(True)
            plt.show()

            # Gráfico 5: Erro (Valor - Preço) em função da diferença (Oferta - Demanda)
            diferenca_oferta_demanda = [abs(ofertas[j] - demandas[j]) for j in rodadas]
            plt.figure(figsize=(10, 5))
            plt.plot(diferenca_oferta_demanda, diferenca_valores_precos, 'o-', color='orange',
                     label='Erro vs Oferta-Demanda')
            plt.title(f'Aproximação dos Valores aos Preços conforme Oferta se aproxima de Demanda para {bem}')
            plt.xlabel('Erro (|Oferta - Demanda|)')
            plt.ylabel('Erro Absoluto (|Valor - Preço|)')
            plt.legend()
            plt.grid(True)
            plt.show()


    def plotar_curva_lorenz(self,agentes):
        # 1. Extraímos as rendas de cada agente
        rendas = [agente.dinheiro for agente in agentes]

        # 2. Ordenamos as rendas em ordem crescente
        rendas_ordenadas = sorted(rendas)

        # 3. Calculamos a renda acumulada
        renda_acumulada = np.cumsum(rendas_ordenadas)
        renda_total = renda_acumulada[-1]  # Renda total de todos os agentes
        porcentagem_renda_acumulada = renda_acumulada / renda_total

        # 4. Calculamos a proporção de agentes
        num_agentes = len(agentes)
        proporcao_agentes = np.arange(1, num_agentes + 1) / num_agentes

        # 5. Plotamos a curva de Lorenz
        plt.figure(figsize=(8, 6))
        plt.plot(proporcao_agentes, porcentagem_renda_acumulada, label="Curva de Lorenz", color="blue")

        # Linha de igualdade perfeita (45º) para comparação
        plt.plot([0, 1], [0, 1], label="Igualdade Perfeita", color="red", linestyle="--")

        plt.title('Curva de Lorenz - Concentração de Renda')
        plt.xlabel('Proporção de Agentes')
        plt.ylabel('Proporção de Renda Acumulada')
        plt.legend()
        plt.grid(True)
        plt.show()


# Exemplo de uso:
mercado = Mercado(num_agentes=20, num_dinheiro=1000, num_mercadorias=10)
mercado.rodar(700)