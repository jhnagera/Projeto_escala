from flask import Flask, request, jsonify
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuração do Banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123@localhost/gestao_escalas'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Boa prática desativar isso se não usar signals
db = SQLAlchemy(app)

# --- ROTAS ---

# 1. CRIAR (INSERT)
@app.route("/funcionarios", methods=["POST"])
def criar():
    try:
        nome = request.form.get("nome")
        horario_inicio = request.form.get("horario_inicio")
        horario_fim = request.form.get("horario_fim")

        sql = text("INSERT INTO funcionarios (nome, horario_inicio, horario_fim) VALUES (:nome, :horario_inicio, :horario_fim)")
        dados = {"nome": nome, "horario_inicio": horario_inicio, "horario_fim": horario_fim}

        db.session.execute(sql, dados)
        db.session.commit()

        return jsonify({"mensagem": f"Funcionário {nome} criado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# 2. CRIAR COM ID (RETURNING)
@app.route("/funcionarioID", methods=["POST"])
def criarComId():
    try:
        nome = request.form.get("nome")
        horario_inicio = request.form.get("horario_inicio")
        horario_fim = request.form.get("horario_fim")

        sql = text("INSERT INTO funcionarios (nome, horario_inicio, horario_fim) VALUES (:nome, :horario_inicio, :horario_fim) RETURNING id")
        dados = {"nome": nome, "horario_inicio": horario_inicio, "horario_fim": horario_fim}

        result = db.session.execute(sql, dados)
        db.session.commit()

        # Pega o ID gerado
        novo_id = result.fetchone()[0]
        dados['id'] = novo_id

        return jsonify(dados), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# 3. LER UM (SELECT BY ID)
@app.route("/funcionarios/<id>", methods=["GET"])
def get_one(id):
    sql = text("SELECT * FROM funcionarios where id = :id")
    dados = {"id": id}
    
    try:
        result = db.session.execute(sql, dados)
        lista_resultados = result.mappings().all()

        if len(lista_resultados) > 0:
            # 1. Converte a linha do banco para um dicionário Python comum
            funcionario_dict = dict(lista_resultados[0])

            # 2. Converte os objetos de TEMPO para STRING (Texto)
            # "str()" transforma o objeto datetime.time(8,0) em "08:00:00"
            if funcionario_dict.get('horario_inicio'):
                funcionario_dict['horario_inicio'] = str(funcionario_dict['horario_inicio'])
            
            if funcionario_dict.get('horario_fim'):
                funcionario_dict['horario_fim'] = str(funcionario_dict['horario_fim'])

            return jsonify(funcionario_dict)
        else:
            return jsonify({"mensagem": "Funcionário não encontrado"}), 404
            
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# 4. LER TODOS (SELECT ALL)
@app.route("/funcionarios", methods=["GET"])
def get_all():
    sql_query = text("SELECT * FROM funcionarios")
    
    try:
        result = db.session.execute(sql_query)
        relatorio = result.mappings().all()
        
        lista_funcionarios = []

        for row in relatorio:
            # 1. Converte a linha para dicionário
            funcionario_dict = dict(row)

            # 2. Converte os horários para string em cada funcionário
            if funcionario_dict.get('horario_inicio'):
                funcionario_dict['horario_inicio'] = str(funcionario_dict['horario_inicio'])
            
            if funcionario_dict.get('horario_fim'):
                funcionario_dict['horario_fim'] = str(funcionario_dict['horario_fim'])

            # 3. Adiciona na lista final
            lista_funcionarios.append(funcionario_dict)

        return jsonify(lista_funcionarios)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# 5. ATUALIZAR (UPDATE)
@app.route("/funcionarios/<id>", methods=["PUT"])
def atualizar(id):
    try:
        nome = request.form.get("nome")
        horario_inicio = request.form.get("horario_inicio")
        horario_fim = request.form.get("horario_fim")

        sql = text("UPDATE funcionarios SET nome = :nome, horario_inicio = :horario_inicio, horario_fim = :horario_fim WHERE id = :id")
        
        # CORREÇÃO CRÍTICA: Adicionado o ID no dicionário de dados
        dados = {
            "id": id,
            "nome": nome, 
            "horario_inicio": horario_inicio, 
            "horario_fim": horario_fim
        }

        result = db.session.execute(sql, dados)
        
        if result.rowcount == 1: 
            db.session.commit()
            return jsonify({"mensagem": f"Funcionário {id} atualizado com sucesso"}), 200
        else:
            db.session.rollback()
            return jsonify({"mensagem": "Funcionário não encontrado ou erro ao atualizar"}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

# 6. DELETAR (DELETE)
@app.route("/funcionarios/<id>", methods=['DELETE'])
def delete(id):
    try:
        sql = text("DELETE FROM funcionarios WHERE id = :id")
        dados = {"id": id}
        
        result = db.session.execute(sql, dados)

        if result.rowcount == 1: 
            db.session.commit()
            return jsonify({"mensagem": f"Funcionário {id} removido"}), 200
        else:
            db.session.rollback()
            return jsonify({"mensagem": "Funcionário não encontrado"}), 404
            
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)