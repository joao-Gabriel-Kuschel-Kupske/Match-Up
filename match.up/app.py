from flask import Flask, render_template, request, redirect, url_for, send_file
import csv
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user 

# -----------------
# -- CONFIGURAÇÃO -
# -----------------

app = Flask(__name__)
CSV_FILENAME = 'dados.csv'
app.config['SECRET_KEY'] = 'chave_simples_e_secreta_para_sessao' 

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'formulario_login'

# -----------------
# -- GERENCIAMENTO DE USUÁRIOS (SIMPLES) ---
# -----------------

class User(UserMixin):
    """Classe que representa um usuário para o Flask-Login."""
    def __init__(self, id, email, password, nome):
        self.id = id
        self.email = email
        self.password = password
        self.nome = nome

    def get_id(self):
        return str(self.id)

# Variável global para usuários carregados
USERS = {} 

def ensure_csv_header():
   """Garante que o arquivo CSV exista com o cabeçalho correto."""
   if not os.path.exists(CSV_FILENAME):
       try:
           with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
               writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
               writer.writerow(['Data', 'Nome', 'Email', 'Senha'])
       except Exception as e:
           print(f"ERRO: Não foi possível criar o arquivo CSV: {e}")

def load_initial_users_from_csv():
    """Carrega todos os usuários do CSV para a memória na inicialização."""
    global USERS
    USERS = {}
    ensure_csv_header()
    if os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            user_id = 1
            for row in reader:
                # Ignora a linha de cabeçalho e garante que a linha tem dados
                if 'Email' in row and row['Email']:
                    user_id_str = str(user_id)
                    USERS[user_id_str] = User(
                        id=user_id_str,
                        email=row['Email'],
                        password=row['Senha'],
                        nome=row['Nome']
                    )
                    user_id += 1

# User Loader: Funções que o Flask-Login usa para encontrar um usuário
@login_manager.user_loader
def load_user(user_id):
    """Retorna um objeto User dado o user_id armazenado na sessão."""
    return USERS.get(user_id)

# -----------------
# -- ROTAS GERAIS -
# -----------------

@app.route('/')
def inicio():
   return render_template('index.html')

@app.route('/entrar')
def entrar():
   # Redireciona para login se não estiver autenticado
   if not current_user.is_authenticated:
       return redirect(url_for('formulario_login'))
   return redirect(url_for('pagcursos'))

@app.route('/formulario_cadastro')
def formulario():
   return render_template('cadastro.html')

# -----------------
# -- ROTAS DE AUTENTICAÇÃO -----
# -----------------

@app.route('/formulario_login', methods=['GET', 'POST'])
def formulario_login():
   if current_user.is_authenticated:
       return redirect(url_for('area_aluno'))

   if request.method == 'POST':
       email = request.form.get('email')
       senha_input = request.form.get('senha')
       
       # Busca o usuário pelo email
       user_found = next((user for user in USERS.values() if user.email == email), None)

       # Verifica se o usuário existe e se a senha confere
       if user_found and user_found.password == senha_input: 
           login_user(user_found) # FAZ O LOGIN
           return redirect(url_for('area_aluno'))
       else:
           # Mantém o usuário na tela de login com uma mensagem de erro
           return render_template('login.html', erro='Email ou Senha incorretos.')
            
   return render_template('login.html')

@app.route('/logout')
@login_required 
def logout():
    logout_user() # ENCERRA A SESSÃO
    return redirect(url_for('inicio'))

# -----------------
# -- CADASTRO -----
# -----------------

@app.route('/salvar_dados', methods=['POST'])
def salvar_dados():
   try:
       nome = request.form.get('nome')
       email = request.form.get('email')
       senha = request.form.get('senha')
       data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

       if not nome or not email or not senha:
           return "ERRO: Todos os campos são obrigatórios.", 400

       ensure_csv_header() 

       with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
           writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
           writer.writerow([data_registro, nome, email, senha])
           
       # Recarrega a lista de usuários em memória para incluir o novo registro
       load_initial_users_from_csv() 

       return redirect(url_for('formulario_login'))
           
   except Exception as e:
       print(f"ERRO ao salvar no CSV: {e}")
       return f"Ocorreu um erro interno ao salvar seu cadastro: {e}", 500

# -----------------
# -- ROTAS PROTEGIDAS --------
# -----------------

@app.route('/fração-class')
@login_required # PROTEGIDA
def aula_fra():
   return render_template('fracao.html')

@app.route('/múltiplos-e-divisores-class')
@login_required # PROTEGIDA
def aula_mult_e_div():
   return render_template('mult-e-div.html')

@app.route('/equação-de-1°-grau-class')
@login_required # PROTEGIDA
def aula_1_equa():
   return render_template('1equacao.html')

@app.route('/ângulos-class')
@login_required # PROTEGIDA
def aula_ang():
   return render_template('angulos.html')

@app.route('/geometria-class')
@login_required # PROTEGIDA
def aula_geom():
   return render_template('geometria.html')

@app.route('/sistema-numérico-class')
@login_required # PROTEGIDA
def aula_sisenum():
   return render_template('sisenum.html')

@app.route('/area_aluno')
@login_required # PROTEGIDA
def area_aluno():
   # current_user.nome estará disponível aqui
   return render_template("perfil.html", user=current_user)

@app.route('/aula/<nome>')
@login_required # PROTEGIDA
def abrir_aula(nome):
    pdf_path = os.path.join("static", "aulas", nome + ".pdf")
    return send_file(pdf_path, mimetype='application/pdf', as_attachment=False)

@app.route("/pagcursos")
@login_required # PROTEGIDA
def pagcursos():
    arquivos = os.listdir('static/aulas')
    aulas = [a.replace(".pdf", "") for a in arquivos]
    return render_template("pagcursos.html", aulas=aulas)

# -----------------
# -- EXECUÇÃO -----
# -----------------

if __name__ == "__main__":
   load_initial_users_from_csv() # Carrega os usuários no início
   app.run(debug=True)