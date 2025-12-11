from datetime import datetime, timedelta
import random

def gerar_escala_balanceada(hora_inicio_escala_str, hora_fim_escala_str, intervalo_minutos, postos_rodizio, postos_fixos, agenda_funcionarios, postos_prioridade, min_passagens):
    """
    Gera uma escala de serviço com rodízio e alocações fixas, garantindo 
    que os funcionários passem um número mínimo de vezes pelos postos de prioridade.
    
    :param postos_prioridade: Lista de nomes de postos que devem ser balanceados (ex: ["Alfa 2", "Alfa 3"]).
    :param min_passagens: Número mínimo de vezes que cada funcionário deve passar nos postos de prioridade.
    ...
    """
    
    # Define a data base (a data real não importa, só o tempo)
    hoje = datetime.now().date()
    intervalo = timedelta(minutes=intervalo_minutos)
    hora_fim_escala = datetime.combine(hoje, datetime.strptime(hora_fim_escala_str, "%H:%M").time())
    
    # 1. Preparar os tempos de entrada e saída e definir nomes de rodízio
    tempos_entrada = {}
    tempos_saida = {}
    nomes_rodizio = [nome for nome in agenda_funcionarios.keys() if nome not in postos_fixos.values()]
    
    for nome, (start_str, end_str) in agenda_funcionarios.items():
        tempos_entrada[nome] = datetime.combine(hoje, datetime.strptime(start_str, "%H:%M").time())
        tempos_saida[nome] = datetime.combine(hoje, datetime.strptime(end_str, "%H:%M").time())

    nomes_postos = list(postos_rodizio.keys()) + list(postos_fixos.keys())
    
    # Mapeia a ordem dos postos de rodízio para seus nomes
    ordem_postos_rodizio = list(postos_rodizio.keys())
    
    # Inicializa o histórico de passagens nos postos de prioridade
    historico_posto = {nome: {posto: 0 for posto in postos_prioridade} for nome in nomes_rodizio}
    
    # Cabeçalho e inicialização do loop
    escala_tabela = [["Horário"] + nomes_postos]
    tempo_atual = datetime.combine(hoje, datetime.strptime(hora_inicio_escala_str, "%H:%M").time())
    funcionarios_atuais = [] # Lista que representa a fila de rodízio (ordem de prioridade)

    # Loop principal
    while tempo_atual < hora_fim_escala:
        
        # 1. REMOÇÃO: Funcionários do RODÍZIO que saem
        funcionarios_atuais = [
            f for f in funcionarios_atuais 
            if tempos_saida.get(f) is None or tempos_saida[f] > tempo_atual 
        ]
        
        # 2. ADIÇÃO: Funcionários do RODÍZIO que entram
        for nome, hora_entrada in tempos_entrada.items():
            if nome in nomes_rodizio and hora_entrada == tempo_atual and nome not in funcionarios_atuais:
                funcionarios_atuais.append(nome)
        
        # 3. LÓGICA DE PRIORIZAÇÃO (ANTES DA DESIGNAÇÃO)
        
        # Identifica os funcionários que precisam passar mais vezes pelos postos prioritários
        funcionarios_a_priorizar = []
        for nome in funcionarios_atuais:
            if all(historico_posto[nome][posto] < min_passagens for posto in postos_prioridade):
                funcionarios_a_priorizar.append(nome)
        
        # Postos de prioridade na lista de rodízio
        indices_prioridade = [ordem_postos_rodizio.index(p) for p in postos_prioridade if p in ordem_postos_rodizio]
        
        # Se houver funcionários e postos de prioridade disponíveis, ajusta a fila
        if funcionarios_a_priorizar and indices_prioridade:
            # Seleciona o funcionário com menor contagem para ser o próximo a ir para um posto prioritário
            # Prioriza quem tem a menor soma de passagens pelos postos-alvo
            def somar_passagens(nome):
                return sum(historico_posto[nome].values())

            funcionarios_a_priorizar.sort(key=somar_passagens)
            
            # Pega o funcionário mais necessitado e move-o para a posição que será designada ao primeiro posto prioritário
            proximo_a_priorizar = funcionarios_a_priorizar[0]
            
            # Encontra a posição atual do funcionário na fila
            try:
                indice_atual = funcionarios_atuais.index(proximo_a_priorizar)
            except ValueError:
                # O funcionário ainda não está na fila, o que é improvável aqui
                indice_atual = -1 
            
            # Se ele não for o primeiro a ser designado, move ele para a posição ideal
            # A posição ideal é a primeira posição livre que corresponde a um posto prioritário
            if indice_atual > -1 and indice_atual != indices_prioridade[0]:
                funcionarios_atuais.pop(indice_atual)
                funcionarios_atuais.insert(indices_prioridade[0], proximo_a_priorizar)
        
        # 4. DESIGNAR POSTOS
        num_postos_rodizio = len(postos_rodizio)
        designacoes_rodizio = funcionarios_atuais[:num_postos_rodizio]
        
        # Atualiza o histórico para o slot atual (antes do rodízio)
        for i, nome in enumerate(designacoes_rodizio):
            posto = ordem_postos_rodizio[i]
            if posto in postos_prioridade and nome in historico_posto:
                historico_posto[nome][posto] += 1
        
        # Marca como VAGO se não houver funcionário suficiente
        vagos = num_postos_rodizio - len(designacoes_rodizio)
        designacoes_rodizio += (["VAGO"] * vagos)

        # Postos Fixos
        designacoes_fixas = list(postos_fixos.values())
        
        # Combina a linha
        linha_designacoes = designacoes_rodizio + designacoes_fixas

        # 5. CRIA A LINHA DA ESCALA
        horario_slot = f"{tempo_atual.strftime('%H:%M')} - {(tempo_atual + intervalo).strftime('%H:%M')}"
        linha = [horario_slot] + linha_designacoes
        escala_tabela.append(linha)
        
        # 6. RODÍZIO: Último vai para o primeiro (apenas no pool de rodízio)
        if funcionarios_atuais:
            ultimo_funcionario = funcionarios_atuais.pop()
            funcionarios_atuais.insert(0, ultimo_funcionario)

        # 7. AVANÇA TEMPO
        tempo_atual += intervalo

    return escala_tabela

# --- Configurações da Escala ---
HORA_INICIO = "12:30"
HORA_FIM = "18:30" 
INTERVALO_MINUTOS = 30

# NOVO: Parâmetros para balanceamento
POSTOS_PRIORIDADE = ["Alfa 2", "Alfa 3"]
MIN_PASSAGENS = 3

# 1. DEFINIÇÃO DOS POSTOS FIXOS E DE RODÍZIO
# Postos de rodízio (P1 a P7)
POSTOS_RODIZIO = {
    "Alfa 2": "",      # P1 (Índice 0)
    "Ronda P1": "",    # P2 (Índice 1)
    "Delta 4": "",     # P3 (Índice 2)
    "Alfa 3": "",      # P4 (Índice 3)
    "Ronda P2 e P3": "", # P5 (Índice 4)
    "Galeria/QAP": "", # P6 (Índice 5)
    "Monitoramento": "" # P7 (Índice 6)
}

# Posto Fixo (P8)
POSTOS_FIXOS = {
    "Central": "Henrique/Melissa"
}

# 2. AGENDA COM HORÁRIO DE ENTRADA E SAÍDA DE TODOS os funcionários
FUNCIONARIOS_SCHEDULE = {
    "Manuel": ("12:30", "18:30"), "Melero": ("12:30", "13:30"), "Nereu": ("12:30", "13:30"), 
    "Mirales": ("12:30", "18:30"), "Hamilton": ("12:30", "18:30"),
    "Marcelo": ("13:00", "19:00"), "Faustino": ("13:00", "19:00"), "Maia": ("13:00", "19:00"), 
    "Bursi": ("13:00", "19:00"), "Augusto": ("14:00", "20:00"),
    "Menezes": ("12:30", "15:30"),
    "Henrique/Melissa": ("13:00", "18:30") 
}

# --- Geração e Exibição ---
escala = gerar_escala_balanceada(
    HORA_INICIO, 
    HORA_FIM, 
    INTERVALO_MINUTOS, 
    POSTOS_RODIZIO, 
    POSTOS_FIXOS, 
    FUNCIONARIOS_SCHEDULE,
    POSTOS_PRIORIDADE,
    MIN_PASSAGENS
)

print("\n--- ESCALA COM PRIORIZAÇÃO DE POSTOS (Alfa 2 e Alfa 3) ---\n")
for linha in escala:
    print(" | ".join(linha))