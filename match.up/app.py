from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import csv
import os
from datetime import datetime

# -----------------
# -- CONFIGURAÇÃO -
# -----------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_necessaria'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'formulario_login'

CSV_FILENAME = 'usuarios.csv'
AVALIACAO_FILENAME = 'avaliacao.csv'
USERS = {}

# -----------------
# -- GERENCIAMENTO DE USUÁRIOS -
# -----------------

class User(UserMixin):
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
                header = next(reader, None)
                if header and header == ['data_registro', 'nome', 'email', 'senha']:
                    for i, row in enumerate(reader, start=1):
                        if len(row) == 4:
                            data_registro, nome, email, senha = row
                            user_id = str(i)
                            USERS[user_id] = User(user_id, nome, email, senha)
                else:
                    ensure_csv_header() 
        except Exception as e:
            print(f"AVISO: Não foi possível ler o CSV de usuários: {e}")

def ensure_avaliacao_header():
    """Garante que o arquivo de avaliações tenha o cabeçalho correto."""
    if not os.path.exists(AVALIACAO_FILENAME) or os.path.getsize(AVALIACAO_FILENAME) == 0:
        with open(AVALIACAO_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'data_registro', 'nome', 'email',
                'Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m'
            ])

def atualizar_avaliacao(coluna, rating):
    """Atualiza ou cria a avaliação do usuário na coluna especificada."""
    data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ensure_avaliacao_header()

    rows = []
    updated = False

    with open(AVALIACAO_FILENAME, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['email'].lower() == current_user.email.lower():
                row[coluna] = rating
                row['data_registro'] = data_registro
                updated = True
            rows.append(row)

    if not updated:
        nova_linha = {
            'data_registro': data_registro,
            'nome': current_user.nome,
            'email': current_user.email,
            'Av_f': '',
            'Av_s': '',
            'Av_e': '',
            'Av_a': '',
            'Av_g': '',
            'Av_m': ''
        }
        nova_linha[coluna] = rating
        rows.append(nova_linha)

    with open(AVALIACAO_FILENAME, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['data_registro','nome','email','Av_f','Av_s','Av_e','Av_a','Av_g','Av_m']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def ensure_csv_header():
    """Garante que o arquivo CSV exista com o cabeçalho correto."""
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
   return render_template('testesimples.html')

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
       
       user_found = next((user for user in USERS.values() 
                           if user.email.lower() == email_input.lower()), None)
       
       if user_found and user_found.password == senha_input: 
           login_user(user_found) 
           return redirect(url_for('pagcursos')) 
       else:
           return render_template('login.html', erro='Email ou Senha incorretos.')
            
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

       if any(user.email.lower() == email.lower() for user in USERS.values()):
           return f"ERRO: O e-mail {email} já está cadastrado.", 400

       ensure_csv_header() 

       with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
           writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
           writer.writerow([data_registro, nome, email, senha])
           
       load_initial_users_from_csv() 

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

# FUNÇÃO AUXILIAR PARA EVITAR REPETIÇÃO DE CÓDIGO NAS ROTAS DE AULA
def get_media_data(col_key):
    """Chama o cálculo de médias e extrai os dados de uma coluna específica."""
    medias = calcular_medias_por_categoria()
    # Retorna o dicionário de média/total ou {0.0, 0} se não houver dados.
    return medias.get(col_key, {'media': 0.0, 'total': 0})

@app.route('/fração-class')
@login_required 
def aula_fra():
    # CORREÇÃO APLICADA AQUI: Busca a média de Av_f e passa para o template
    dados_fracao = get_media_data('Av_f')
    return render_template(
        'fracao.html', 
        user=current_user,
        media_modulo=dados_fracao['media'],
        total_modulo=dados_fracao['total']
    )

@app.route('/múltiplos-e-divisores-class')
@login_required 
def aula_mult_e_div():
    dados_modulo = get_media_data('Av_m')
    return render_template(
        'mult-e-div.html', 
        user=current_user,
        media_modulo=dados_modulo['media'],
        total_modulo=dados_modulo['total']
    )

@app.route('/equação-de-1°-grau-class')
@login_required 
def aula_1_equa():
    dados_modulo = get_media_data('Av_e')
    return render_template(
        '1equacao.html', 
        user=current_user,
        media_modulo=dados_modulo['media'],
        total_modulo=dados_modulo['total']
    )

@app.route('/ângulos-class')
@login_required 
def aula_ang():
    dados_modulo = get_media_data('Av_a')
    return render_template(
        'angulos.html', 
        user=current_user,
        media_modulo=dados_modulo['media'],
        total_modulo=dados_modulo['total']
    )

@app.route('/geometria-class')
@login_required 
def aula_geom():
    dados_modulo = get_media_data('Av_g')
    return render_template(
        'geometria.html', 
        user=current_user,
        media_modulo=dados_modulo['media'],
        total_modulo=dados_modulo['total']
    )

@app.route('/sistema-numérico-class')
@login_required 
def aula_sisenum():
    dados_modulo = get_media_data('Av_s')
    return render_template(
        'sisenum.html', 
        user=current_user,
        media_modulo=dados_modulo['media'],
        total_modulo=dados_modulo['total']
    )

@app.route('/area_aluno')
@login_required 
def area_aluno():
   return render_template("perfil.html", user=current_user)

@app.route("/pagcursos")
@login_required 
def pagcursos():
    return render_template("pagcursos.html")

# -----------------
# -- AVALIAÇÃO -----
# -----------------

@app.route('/avaliar_fra', methods=['POST'])
@login_required
def avaliar_fra():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_f', rating)
    return redirect(url_for('aula_fra'))

@app.route('/avaliar_sisenum', methods=['POST'])
@login_required
def avaliar_sisenum():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_s', rating)
    return redirect(url_for('aula_sisenum'))

@app.route('/avaliar_1grau', methods=['POST'])
@login_required
def avaliar_1grau():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_e', rating)
    return redirect(url_for('aula_1_equa'))

@app.route('/avaliar_ang', methods=['POST'])
@login_required
def avaliar_ang():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_a', rating)
    return redirect(url_for('aula_ang'))

@app.route('/avaliar_geom', methods=['POST'])
@login_required
def avaliar_geom():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_g', rating)
    return redirect(url_for('aula_geom'))

@app.route('/avaliar_mult_div', methods=['POST'])
@login_required
def avaliar_mult_div():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_m', rating)
    return redirect(url_for('aula_mult_e_div'))


# -----------------------
# -- Media avaliação-----
# -----------------------

def calcular_medias_por_categoria():
    """Calcula e retorna a média e o total de pontuações para cada categoria individualmente."""
    
    colunas_avaliacao = ['Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m']
    dados_por_categoria = {col: {'soma': 0, 'total': 0} for col in colunas_avaliacao}

    if not os.path.exists(AVALIACAO_FILENAME):
        return {col: {'media': 0.0, 'total': 0} for col in colunas_avaliacao}

    try:
        with open(AVALIACAO_FILENAME, mode='r', newline='', encoding='utf-8') as arquivo_csv:
            leitor = csv.DictReader(arquivo_csv)
            
            for row in leitor:
                for coluna in colunas_avaliacao:
                    pontuacao_str = row.get(coluna, '').strip()
                    
                    if pontuacao_str:
                        try:
                            # Tenta converter a pontuação para inteiro (para somar)
                            pontuacao = int(pontuacao_str) 
                            dados_por_categoria[coluna]['soma'] += pontuacao
                            dados_por_categoria[coluna]['total'] += 1
                        except ValueError:
                            # Ignora pontuações inválidas
                            continue
            
            resultados_finais = {}
            for coluna, dados in dados_por_categoria.items():
                soma = dados['soma']
                total = dados['total']
                
                media = round(soma / total, 2) if total > 0 else 0.0
                
                resultados_finais[coluna] = {
                    'media': media,
                    'total': total
                }
                
            return resultados_finais
                
    except IOError:
        return {col: {'media': 0.0, 'total': 0} for col in colunas_avaliacao}

@app.route('/media_avaliacoes')
@login_required
def media_avaliacoes():
    """Rota para exibir as médias de avaliação por categoria."""
    
    
    medias_por_categoria = calcular_medias_por_categoria()
    
    
    nomes_amigaveis = {
        'Av_f': 'Fração',
        'Av_s': 'Sistema Numérico',
        'Av_e': 'Equação de 1° Grau',
        'Av_a': 'Ângulos',
        'Av_g': 'Geometria',
        'Av_m': 'Múltiplos e Divisores'
    }
    
    # Renderiza um template e passa os dados
    return render_template(
        'media_avaliacoes.html', 
        medias=medias_por_categoria,
        nomes=nomes_amigaveis
    )

# -----------------
# -- EXECUÇÃO -----
# -----------------

if __name__ == '__main__':
    # Cria o arquivo de avaliações, se não existir, antes de iniciar o app
    ensure_avaliacao_header()
    app.run(debug=True)