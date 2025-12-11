from flask import Flask, request, jsonify
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy #importar certinho
import psycopg2
from psycopg2 import sql
import random
from datetime import datetime, date, time

app = Flask(__name__)

#Conexao Geral do meu app
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123@localhost/gestao_escalas'
db = SQLAlchemy(app) #conecta

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# Altere estas configurações para o seu ambiente Postgres local
DB_CONFIG = {
    "dbname": "gestao_escalas",
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """Estabelece conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def setup_database():
    """Cria as tabelas necessárias se não existirem e insere dados iniciais."""
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()

    # 1. Tabela de Postos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS postos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(50) UNIQUE NOT NULL,
            prioridade INTEGER DEFAULT 2 -- 1 = Alta, 2 = Normal
        );
    """)

    # 2. Tabela de Funcionários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            horario_inicio TIME NOT NULL,
            horario_fim TIME NOT NULL
        );
    """)

    # 3. Tabela Cabeçalho da Escala (Dia)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS escalas (
            id SERIAL PRIMARY KEY,
            data_escala DATE UNIQUE NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Tabela Detalhes da Escala (Quem está onde)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS escala_detalhes (
            id SERIAL PRIMARY KEY,
            escala_id INTEGER REFERENCES escalas(id),
            posto_id INTEGER REFERENCES postos(id),
            funcionario_id INTEGER REFERENCES funcionarios(id),
            hora_inicio TIME,
            hora_fim TIME
        );
    """)

    # --- INSERÇÃO DE DADOS PADRÃO (POSTOS) ---
    postos_iniciais = [
        ("Alfa 2", 1),          # Prioridade Alta
        ("Alfa 3", 1),          # Prioridade Alta
        ("Ronda P1", 2),
        ("Delta 4", 2),
        ("Ronda P2", 2),
        ("Ronda P3", 2),
        ("Galeria/QAP", 2),
        ("Monitoramento", 2)
    ]

    for nome, prioridade in postos_iniciais:
        cur.execute("""
            INSERT INTO postos (nome, prioridade) 
            VALUES (%s, %s) 
            ON CONFLICT (nome) DO NOTHING;
        """, (nome, prioridade))

    # --- INSERÇÃO DE DADOS PADRÃO (FUNCIONÁRIOS - EXEMPLO) ---
    # Inserindo 10 funcionários fictícios para cobrir os 8 postos
    funcionarios_teste = [
        ("João Silva", "07:00", "19:00"),
        ("Maria Oliveira", "07:00", "19:00"),
        ("Carlos Santos", "07:00", "19:00"),
        ("Ana Souza", "07:00", "19:00"),
        ("Pedro Lima", "07:00", "19:00"),
        ("Fernanda Costa", "07:00", "19:00"),
        ("Lucas Pereira", "08:00", "20:00"),
        ("Julia Martins", "08:00", "20:00"),
        ("Roberto Alves", "07:00", "19:00"),
        ("Patrícia Gomes", "07:00", "19:00")
    ]

    for func in funcionarios_teste:
        cur.execute("SELECT id FROM funcionarios WHERE nome = %s", (func[0],))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO funcionarios (nome, horario_inicio, horario_fim)
                VALUES (%s, %s, %s)
            """, func)

    conn.commit()
    cur.close()
    conn.close()
    print("Banco de dados configurado e dados iniciais verificados.")

def gerar_escala_do_dia(data_alvo):
    """Gera a escala para uma data específica."""
    conn = get_db_connection()
    if not conn:
        return

    cur = conn.cursor()

    # Verificar se já existe escala para hoje
    cur.execute("SELECT id FROM escalas WHERE data_escala = %s", (data_alvo,))
    exists = cur.fetchone()
    if exists:
        print(f"Atenção: Já existe uma escala para {data_alvo}. Abortando para não duplicar.")
        return

    print(f"--- Gerando escala para {data_alvo} ---")

    # 1. Buscar Postos (Ordenados por Prioridade: 1 vem antes de 2)
    cur.execute("SELECT id, nome, prioridade FROM postos ORDER BY prioridade ASC, id ASC")
    postos = cur.fetchall()

    # 2. Buscar Funcionários Disponíveis
    # Nota: Num cenário real, você filtraria quem está de folga/ferias aqui.
    cur.execute("SELECT id, nome, horario_inicio, horario_fim FROM funcionarios")
    todos_funcionarios = cur.fetchall() # Lista de tuplas

    # 3. Lógica de Distribuição e Rodízio
    # Transformamos em lista mutável para remover conforme alocamos
    funcionarios_disponiveis = list(todos_funcionarios)
    
    # O SHUFFLE é crucial para o "Equilíbrio/Rodízio" aleatório simples.
    # Para um rodízio perfeito, precisaríamos consultar o histórico (quem fez Alfa 2 ontem).
    random.shuffle(funcionarios_disponiveis) 

    escala_gerada = []

    for posto in postos:
        posto_id, posto_nome, posto_prioridade = posto
        
        if not funcionarios_disponiveis:
            print(f"ALERTA: Não há funcionários suficientes para o posto {posto_nome}")
            break

        # Selecionar funcionário
        # Aqui tentamos pegar alguém cujo horário bata com a necessidade do posto (assumindo turno do dia)
        funcionario_escolhido = funcionarios_disponiveis.pop(0)
        
        func_id, func_nome, h_inicio, h_fim = funcionario_escolhido

        escala_gerada.append({
            "posto_id": posto_id,
            "posto_nome": posto_nome,
            "func_id": func_id,
            "func_nome": func_nome,
            "h_inicio": h_inicio,
            "h_fim": h_fim
        })

    # 4. Salvar no Banco
    try:
        # Criar cabeçalho da escala
        cur.execute("INSERT INTO escalas (data_escala) VALUES (%s) RETURNING id", (data_alvo,))
        escala_id = cur.fetchone()[0]

        # Inserir detalhes
        for item in escala_gerada:
            cur.execute("""
                INSERT INTO escala_detalhes (escala_id, posto_id, funcionario_id, hora_inicio, hora_fim)
                VALUES (%s, %s, %s, %s, %s)
            """, (escala_id, item['posto_id'], item['func_id'], item['h_inicio'], item['h_fim']))
        
        conn.commit()
        print(f"Sucesso! Escala ID {escala_id} salva no banco.")
        
        # 5. Imprimir Relatório
        print("\n=== ESCALA FINAL ===")
        print(f"{'POSTO':<20} | {'PRIORIDADE':<10} | {'FUNCIONÁRIO':<20} | {'HORÁRIO'}")
        print("-" * 70)
        for item in escala_gerada:
            prioridade_txt = "ALTA" if item['posto_nome'] in ['Alfa 2', 'Alfa 3'] else "Normal"
            print(f"{item['posto_nome']:<20} | {prioridade_txt:<10} | {item['func_nome']:<20} | {item['h_inicio']} - {item['h_fim']}")
            
    except Exception as e:
        conn.rollback()
        print(f"Erro ao salvar escala: {e}")
    finally:
        cur.close()
        conn.close()

def ler_escala(data_filtro):
    """Função utilitária para ler uma escala do banco."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
        SELECT p.nome, f.nome, ed.hora_inicio, ed.hora_fim
        FROM escala_detalhes ed
        JOIN escalas e ON e.id = ed.escala_id
        JOIN postos p ON p.id = ed.posto_id
        JOIN funcionarios f ON f.id = ed.funcionario_id
        WHERE e.data_escala = %s
        ORDER BY p.prioridade ASC, p.nome ASC;
    """
    cur.execute(query, (data_filtro,))
    rows = cur.fetchall()
    
    if rows:
        print(f"\n--- Lendo do Banco de Dados para {data_filtro} ---")
        for row in rows:
            print(f"Posto: {row[0]} -> {row[1]} ({row[2]} às {row[3]})")
    else:
        print("Nenhuma escala encontrada para esta data.")
    
    conn.close()

if __name__ == "__main__":
    # 1. Configuração Inicial (Executar uma vez)
    setup_database()

    # 2. Definir a data da escala (Hoje)
    hoje = date.today()
    
    # 3. Gerar Escala
    gerar_escala_do_dia(hoje)

    # 4. Verificar leitura
    # ler_escala(hoje)

    if __name__ == "__main__":
        app.run(debug=True)