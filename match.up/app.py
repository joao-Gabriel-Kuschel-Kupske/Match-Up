from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
from datetime import datetime

app = Flask(__name__)
CSV_FILENAME = 'dados.csv'

# ----- Função Auxiliar para o CSV -----
def ensure_csv_header():
   """Garante que o arquivo CSV exista com o cabeçalho correto."""
   if not os.path.exists(CSV_FILENAME):
       try:
           with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
               writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
               # Mantendo a senha em texto puro, conforme sua estrutura
               writer.writerow(['Data', 'Nome', 'Email', 'Senha'])
       except Exception as e:
           print(f"ERRO: Não foi possível criar o arquivo CSV: {e}")

# ----- inicio (index.html) -----
@app.route('/')
def inicio():
   """Rota principal que exibe a página index.html."""
   return render_template('index.html')

# --- pagina de login (pag2.html) -----
# CORREÇÃO 1:
# A função foi renomeada para 'entrar' para bater com o seu url_for('entrar') no index.html
@app.route('/entrar', methods=['GET'])
def entrar():
  
   return render_template('pagcursos.html')

# --- pagina de CADASTRO (cadastro.html) ---
# CORREÇÃO 2:
# Esta rota estava FALTANDO. Ela é necessária para o seu url_for('formulario') no index.html
@app.route('/formulario_cadastro')
def formulario():
   """Exibe o formulário de CADASTRO (cadastro.html)."""
   return render_template('cadastro.html')

@app.route('/formulario_login')
def formulario_login():
   """Exibe o formulário de LOGIN (login.html)."""
   return render_template('login.html')

@app.route('/fração-class')
def aula_fra():
   """Exibe a aula (fracao.html)."""
   return render_template('fracao.html')

@app.route('/múltiplos-e-divisores-class')
def aula_mult_e_div():
   """Exibe a aula (mult-e-div.html)."""
   return render_template('mult-e-div.html')

@app.route('/equação-de-1°-grau-class')
def aula_1_equa():
   """Exibe a aula (1equacao.html)."""
   return render_template('1equacao.html')

@app.route('/ângulos-class')
def aula_ang():
   """Exibe a aula (angulos.html)."""
   return render_template('angulos.html')

@app.route('/geometria-class')
def aula_geom():
   """Exibe a aula (geometria.html)."""
   return render_template('geometria.html')

@app.route('/sistema-numérico-class')
def aula_sisenum():
   """Exibe a aula (sisenum.html)."""
   return render_template('sisenum.html')


# --- Rota para SALVAR os dados do cadastro ---
# CORREÇÃO 3:
# O redirecionamento foi arrumado para 'entrar' (a nova página de login)
@app.route('/salvar_dados', methods=['POST'])
def salvar_dados():
   """Processa os dados do formulário de cadastro.html e salva no CSV."""
   try:
       nome = request.form.get('nome')
       email = request.form.get('email')
       senha = request.form.get('senha')
       data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

       # Validação simples para garantir que os campos não estão vazios
       if not nome or not email or not senha:
           return "ERRO: Todos os campos são obrigatórios.", 400

       ensure_csv_header() # Garante que o arquivo CSV exista

       with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
           writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
           # Salvando a senha em texto puro, conforme solicitado.
           writer.writerow([data_registro, nome, email, senha])
           
       # SUCESSO: Redireciona o usuário para a página de LOGIN (a rota 'entrar')
       return redirect(url_for('entrar'))
           
   except Exception as e:
       print(f"ERRO ao salvar no CSV: {e}")
       return f"Ocorreu um erro interno ao salvar seu cadastro: {e}", 500

# (A rota antiga '/login' foi removida por ser confusa e redundante)

#---- Demais Funções (Rotas de Conteúdo) ------ 
# (Estas rotas estão corretas e não precisam de mudança)

@app.route('/area_aluno')
def area_aluno():
   return render_template("perfil.html")

#------PDF aulas -------
@app.route('/aula/<nome>')
def abrir_aula(nome):
    pdf_path = os.path.join("static", "aulas", nome + ".pdf")
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=False)

@app.route("/entrar")
def pagcursos():
    arquivos = os.listdir('static/aulas')
    aulas = [a.replace(".pdf", "") for a in arquivos]
    return render_template("pagcursos.html", aulas=aulas)

# ---- Execução --------- 

if __name__ == "__main__":
   ensure_csv_header() # Garante o CSV antes de iniciar o app
   app.run(debug=True)
