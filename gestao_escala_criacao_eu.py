from flask import Flask, request, jsonify
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy #importar certinho

app = Flask(__name__)

#Conexao Geral do meu app
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:123@localhost/gestao_escalas'
db = SQLAlchemy(app) #conecta



#CRUD
#Criar 
#insert - SQL
#http/web - POST
@app.route("/funcionarios", methods=["POST"])
def criar():
    #dados que vieram
    nome = request.form.get("nome")
    horario_inicio = request.form.get("horario_inicio")
    horario_fim = request.form.get("horario_fim")

    #SQL
    sql = text("INSERT INTO funcionarios (nome, horario_inicio, horario_fim) VALUES (:nome, :horario_inicio, :horario_fim)")
    dados = {"nome": nome, "horario_inicio": horario_inicio, "horario_fim": horario_fim} #os dados do que veio lá da var sql

    #executar consulta
    result = db.session.execute(sql, dados)
    db.session.commit()

    return f"criado com sucesso {nome} e {horario_inicio} e {horario_fim}"

@app.route("/funcionarioID", methods=["POST"])
def criarComId():
    #dados que vieram
    nome = request.form.get("nome")
    horario_inicio = request.form.get("horario_inicio")
    horario_fim = request.form.get("horario_fim")

    #SQL
    sql = text("INSERT INTO funcionarios (nome, horario_inicio, horario_fim) VALUES (:nome, :horario_inicio, :horario_fim) RETURNING id")
    dados = {"nome": nome, "horario_inicio": horario_inicio, "horario_fim": horario_fim} #os dados do que veio lá da var sql

    #executar consulta
    result = db.session.execute(sql, dados)
    db.session.commit()#commit é "lento"

    #pega o id
    id = result.fetchone()[0]
    dados['id'] = id


    return dados

#Selects

#ver funcionarios
@app.route("/funcionarios/<id>")
def get_one(id):
    sql = text("SELECT * FROM funcionarios where id = :id")
    dados = {"id": id}
    
    try:
        result = db.session.execute(sql, dados)
        #Mapear todas as colunas para a linha
        linha = result.mappings().all()[0]
        print(linha)
        return dict(linha)
    except Exception as e:
        return e

#verTodas os funcionarios
@app.route("/funcionarios")
def get_all():
    sql_query = text("SELECT * FROM funcionarios")
    
    try:
        #result sem dados
        result = db.session.execute(sql_query)
                
        relatorio = result.mappings().all()
        json = [dict(row) for row in relatorio] #Gambi pq cada linha é um objeto

        return json
    except Exception as e:
        return e

#atualizar 
#update => em RESTFull =>  é o PUT
@app.route("/funcionarios/<id>", methods=["PUT"])
def atualizar(id):
    #dados que vieram
    nome = request.form.get("nome")
    horario_inicio = request.form.get("horario_inicio")
    horario_fim = request.form.get("horario_fim")

    sql = text("UPDATE funcionarios SET nome = :nome, horario_inicio = :horario_inicio, horario_fim = :horario_fim WHERE id = :id")
    dados = {"nome": nome, "horario_inicio": horario_inicio, "horario_fim": horario_fim}#os dados do que veio lá da var sql

    result = db.session.execute(sql, dados)

    linhas_afetadas = result.rowcount #conta quantas linhas foram afetadas
    
    if linhas_afetadas == 1: 
        db.session.commit()
        return f"Funcionário com o {id} atualizado"
    else:
        db.session.rollback()
        return f"problemas ao atualizar dados"





#deletar/Destruir
#delete
#deletar/Destruir
#delete
@app.route("/marca/<id>", methods=['DELETE'])
def delete(id):
    sql = text("DELETE FROM marca WHERE id = :id")
    dados = {"id": id}
    result = db.session.execute(sql, dados)

    linhas_afetadas = result.rowcount #conta quantas linhas foram afetadas
    
    if linhas_afetadas == 1: 
        db.session.commit()
        return f"Marca com o {id} removida"
    else:
        db.session.rollback()
        return f"Só deus na causa"

if __name__ == "__main__":
    app.run(debug=True)