from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import csv
import os
from datetime import datetime

# -----------------
# -- CONFIGURAÇÃO -
# -----------------

# CORREÇÃO: __name__ (com dois sublinhados)
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_necessaria'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'formulario_login'

CSV_FILENAME = 'usuarios.csv'
USERS = {}

# -----------------
# -- GERENCIAMENTO DE USUÁRIOS -
# -----------------

class User(UserMixin):
    # CORREÇÃO: __init__ (com dois sublinhados)
    def __init__(self, id, nome, email, password):
        self.id = id
        self.nome = nome
        self.email = email
        self.password = password

def load_initial_users_from_csv():
    """Carrega usuários do CSV para a memória (dicionário USERS)."""
    global USERS
    USERS.clear()
    if os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Pula o cabeçalho
                header = next(reader, None)
                if header and header == ['data_registro', 'nome', 'email', 'senha']:
                    # O ID do usuário será baseado na linha no CSV
                    for i, row in enumerate(reader, start=1):
                        if len(row) == 4:
                            data_registro, nome, email, senha = row
                            user_id = str(i) # IDs começando de 1
                            USERS[user_id] = User(user_id, nome, email, senha)
                else:
                    # Se o cabeçalho estiver faltando/incorreto, garante que será criado
                    ensure_csv_header() 
        except Exception as e:
            print(f"AVISO: Não foi possível ler o CSV de usuários: {e}")


def ensure_csv_header():
    """Garante que o arquivo CSV exista com o cabeçalho correto."""
    # Se o arquivo não existir OU se existir, mas estiver vazio
    if not os.path.exists(CSV_FILENAME) or os.path.getsize(CSV_FILENAME) == 0:
        with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['data_registro', 'nome', 'email', 'senha'])

@login_manager.user_loader
def load_user(user_id):
    """Função obrigatória para o Flask-Login carregar um usuário pelo ID."""
    return USERS.get(user_id)

# Carrega os usuários na inicialização do script
load_initial_users_from_csv()

# -----------------
# -- ROTAS GERAIS -
# -----------------

@app.route('/')
def inicio():
   return render_template('index.html')

@app.route('/entrar')
def entrar():
   return redirect(url_for('pagcursos'))

@app.route('/formulario_cadastro')
def formulario():
   return render_template('cadastro.html')

# -----------------
# -- ROTAS DE AUTENTICAÇÃO -----
# -----------------

@app.route('/formulario_login', methods=['GET', 'POST'])
def formulario_login():
   
   if request.method == 'POST':
       email_input = request.form.get('email', '').strip()
       senha_input = request.form.get('senha', '').strip()
       
       # Busca o usuário pelo e-mail (case-insensitive)
       user_found = next((user for user in USERS.values() 
                           if user.email.lower() == email_input.lower()), None)
       
       # Verifica se encontrou o usuário E se a senha confere
       if user_found and user_found.password == senha_input: 
           login_user(user_found) 
           # Redireciona para a página de cursos após o login
           return redirect(url_for('pagcursos')) 
       else:
           # Retorna à página de login com mensagem de erro
           return render_template('login.html', erro='Email ou Senha incorretos.')
            
   # Para requisições GET, apenas exibe o formulário
   return render_template('login.html')

@app.route('/salvar_dados', methods=['POST'])
def salvar_dados():
   try:
       nome = request.form.get('nome', '').strip()
       email = request.form.get('email', '').strip()
       senha = request.form.get('senha', '').strip()
       data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

       if not nome or not email or not senha:
           return "ERRO: Todos os campos são obrigatórios.", 400

       # Verifica se o e-mail já está em uso (case-insensitive)
       if any(user.email.lower() == email.lower() for user in USERS.values()):
           return f"ERRO: O e-mail {email} já está cadastrado.", 400

       ensure_csv_header() 

       with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
           writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
           writer.writerow([data_registro, nome, email, senha])
           
       # Recarrega a lista de usuários após o novo registro
       load_initial_users_from_csv() 

       # Redireciona para a página de login
       return redirect(url_for('formulario_login'))
           
   except Exception as e:
       print(f"ERRO ao salvar no CSV: {e}")
       return f"Ocorreu um erro interno ao salvar seu cadastro: {e}", 500

@app.route("/logout")
@login_required
def logout():
    """Faz o logout do usuário e redireciona para a página inicial."""
    logout_user()
    return redirect(url_for('inicio'))

# -----------------
# -- ROTAS PROTEGIDAS (REQUEREM LOGIN) --------
# -----------------

@app.route('/fração-class')
@login_required 
def aula_fra():
   return render_template('fracao.html')

@app.route('/múltiplos-e-divisores-class')
@login_required 
def aula_mult_e_div():
   return render_template('mult-e-div.html')

@app.route('/equação-de-1°-grau-class')
@login_required 
def aula_1_equa():
   return render_template('1equacao.html')

@app.route('/ângulos-class')
@login_required 
def aula_ang():
   return render_template('angulos.html')

@app.route('/geometria-class')
@login_required 
def aula_geom():
   return render_template('geometria.html')

@app.route('/sistema-numérico-class')
@login_required 
def aula_sisenum():
   return render_template('sisenum.html')

@app.route('/area_aluno')
@login_required 
def area_aluno():
   # Passa o objeto do usuário logado para o template
   return render_template("perfil.html", user=current_user)

@app.route("/pagcursos")
@login_required 
def pagcursos():
    return render_template("pagcursos.html")

# -----------------
# -- EXECUÇÃO -----
# -----------------

# CORREÇÃO: __name__ e __main__ (com dois sublinhados)
if __name__ == '__main__':
    app.run(debug=True)