from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
import csv
import os
from datetime import datetime
from uuid import uuid4

# -----------------
# CONFIGURAÇÕES
# -----------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_necessaria'

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads/perfil_fotos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'formulario_login'

CSV_FILENAME = 'usuarios.csv'
AVALIACAO_FILENAME = 'avaliacao.csv'
USERS = {}
DEFAULT_PHOTO_PATH = '/static/assets/imagens/foto-perfil.png' # NOVO CAMINHO PADRÃO

# Funções utilitárias

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(UserMixin):
    def __init__(self, id, nome, email, password, foto_perfil=DEFAULT_PHOTO_PATH):
        self.id = id
        self.nome = nome
        self.email = email
        self.password = password
        self.foto_perfil = foto_perfil

def ensure_csv_header():
    if not os.path.exists(CSV_FILENAME) or os.path.getsize(CSV_FILENAME) == 0:
        with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['data_registro', 'nome', 'email', 'senha', 'foto_perfil'])

def load_initial_users_from_csv():
    global USERS
    USERS.clear()
    ensure_csv_header()
    if os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader, None) # Pula o cabeçalho
                for i, row in enumerate(reader, start=1):
                    data_registro, nome, email, senha = row[0:4]
                    foto_perfil = row[4] if len(row) > 4 else DEFAULT_PHOTO_PATH
                    user_id = str(i)
                    USERS[user_id] = User(user_id, nome, email, senha, foto_perfil)
        except Exception as e:
            print(f"AVISO: Não foi possível ler o CSV de usuários: {e}")

@login_manager.user_loader
def load_user(user_id):
    return USERS.get(user_id)

load_initial_users_from_csv()

# -----------------------------------
# TODAS AS ROTAS PARA ACESSAR PAGINAS
# -----------------------------------

@app.route('/')
def inicio():
   return render_template('index.html')

@app.route('/FAQ')
def perguntas():
   return render_template('FAQ.html')

@app.route('/entrar')
def entrar():
   return redirect(url_for('pagcursos'))

@app.route('/formulario_cadastro')
def formulario():
   return render_template('cadastro.html')

@app.route('/area_aluno')
@login_required
def area_aluno():
   return redirect(url_for('editar_perfil'))

@app.route("/pagcursos")
@login_required
def pagcursos():
    return render_template("pagcursos.html", user=current_user)

# Funções auxiliares para módulos de aula
def get_media_data(col_key):
    medias = calcular_medias_por_categoria()
    return medias.get(col_key, {'media': 0.0, 'total': 0})

@app.route('/fração-class')
@login_required
def aula_fra():
    dados_fracao = get_media_data('Av_f')
    return render_template('fracao.html', user=current_user, media_modulo=dados_fracao['media'], total_modulo=dados_fracao['total'])

@app.route('/múltiplos-e-divisores-class')
@login_required
def aula_mult_e_div():
    dados_modulo = get_media_data('Av_m')
    return render_template('mult-e-div.html', user=current_user, media_modulo=dados_modulo['media'], total_modulo=dados_modulo['total'])

@app.route('/equação-de-1°-grau-class')
@login_required
def aula_1_equa():
    dados_modulo = get_media_data('Av_e')
    return render_template('1equacao.html', user=current_user, media_modulo=dados_modulo['media'], total_modulo=dados_modulo['total'])

@app.route('/ângulos-class')
@login_required
def aula_ang():
    dados_modulo = get_media_data('Av_a')
    return render_template('angulos.html', user=current_user, media_modulo=dados_modulo['media'], total_modulo=dados_modulo['total'])

@app.route('/geometria-class')
@login_required
def aula_geom():
    dados_modulo = get_media_data('Av_g')
    return render_template('geometria.html', user=current_user, media_modulo=dados_modulo['media'], total_modulo=dados_modulo['total'])

@app.route('/sistema-numérico-class')
@login_required
def aula_sisenum():
    dados_modulo = get_media_data('Av_s')
    return render_template('sisenum.html', user=current_user, media_modulo=dados_modulo['media'], total_modulo=dados_modulo['total'])

@app.route('/media_avaliacoes')
@login_required
def media_avaliacoes():
    medias_por_categoria = calcular_medias_por_categoria()
    nomes_amigaveis = {
        'Av_f': 'Fração', 'Av_s': 'Sistema Numérico', 'Av_e': 'Equação de 1° Grau',
        'Av_a': 'Ângulos', 'Av_g': 'Geometria', 'Av_m': 'Múltiplos e Divisores'
    }
    return render_template('media_avaliacoes.html', medias=medias_por_categoria, nomes=nomes_amigaveis)

# -----------------
# CADASTRO
# -----------------

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

        foto_perfil_default = DEFAULT_PHOTO_PATH # NOVO CAMINHO PADRÃO APLICADO

        with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([data_registro, nome, email, senha, foto_perfil_default])

        load_initial_users_from_csv()

        return redirect(url_for('formulario_login'))

    except Exception as e:
        print(f"ERRO ao salvar no CSV: {e}")
        return f"Ocorreu um erro interno ao salvar seu cadastro: {e}", 500

# -----------------
# LOGIN
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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('inicio'))

# -----------------
# ATUALIZAÇÃO DO PERFIL
# -----------------

def get_all_users_from_csv():
    rows = []
    if os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                rows.append(row)
    return rows

def handle_profile_picture_upload(file):
    foto_perfil_path = current_user.foto_perfil

    if file and file.filename != '' and allowed_file(file.filename):
        try:
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = str(uuid4()) + '.' + extension
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(filepath)

            new_path = f'/static/uploads/perfil_fotos/{filename}'

            # NOVO CAMINHO PADRÃO APLICADO
            default_path = DEFAULT_PHOTO_PATH
            if current_user.foto_perfil and current_user.foto_perfil != default_path:
                try:
                    old_filename = current_user.foto_perfil.split('/')[-1]
                    # Garante que o arquivo a ser deletado está na pasta correta de UPLOAD
                    if old_filename != 'foto-perfil.png': 
                        old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                except Exception as e:
                    print(f"AVISO: Não foi possível deletar a foto antiga: {e}")

            return new_path, None

        except Exception as e:
            return foto_perfil_path, f"Erro ao fazer upload da foto: {e}"

    return foto_perfil_path, None

def update_user_in_csv(old_email, new_nome, new_email, new_password, new_foto_perfil):
    all_users = get_all_users_from_csv()
    updated = False

    for user_data in all_users:
        if user_data['email'].lower() == old_email.lower():
            if new_email.lower() != old_email.lower() and any(
                u['email'].lower() == new_email.lower() for u in all_users if u['email'].lower() != old_email.lower()
            ):
                return False, "ERRO: O novo e-mail já está em uso por outro usuário."

            user_data['nome'] = new_nome
            user_data['email'] = new_email
            user_data['senha'] = new_password if new_password else user_data['senha']
            user_data['foto_perfil'] = new_foto_perfil
            updated = True
            break

    if updated:
        fieldnames = ['data_registro', 'nome', 'email', 'senha', 'foto_perfil']
        with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users)

        load_initial_users_from_csv()

        user_reloaded = next((user for user in USERS.values()
                           if user.email.lower() == new_email.lower()), None)

        if user_reloaded:
            login_user(user_reloaded)
            return True, "Perfil atualizado com sucesso!"
        else:
            return False, "Erro desconhecido ao recarregar o perfil após atualização."

    return False, "Usuário não encontrado para atualização."

@app.route('/editar_perfil', methods=['GET'])
@login_required
def editar_perfil():
    mensagem = request.args.get('mensagem_sucesso')
    erro = request.args.get('mensagem_erro')
    return render_template('perfil.html', user=current_user, mensagem_sucesso=mensagem, mensagem_erro=erro)

@app.route("/atualizap", methods=['GET', 'POST'])
@login_required
def att_perfil_page():
    if request.method == 'POST':
        novo_nome = request.form.get('nome', '').strip()
        novo_email = request.form.get('email', '').strip()
        nova_senha = request.form.get('nova_senha', '').strip()
        senha_atual_confirmacao = request.form.get('senha_atual', '').strip()

        if senha_atual_confirmacao != current_user.password:
            erro = "A senha atual fornecida está incorreta."
            return render_template('att_perfil.html', user=current_user, mensagem_erro=erro)

        foto_file = request.files.get('foto_perfil')
        foto_perfil_path, upload_erro = handle_profile_picture_upload(foto_file)

        if upload_erro:
            return render_template('att_perfil.html', user=current_user, mensagem_erro=upload_erro)

        sucesso, resultado_msg = update_user_in_csv(
            current_user.email,
            novo_nome,
            novo_email,
            nova_senha,
            foto_perfil_path
        )

        if sucesso:
            return redirect(url_for('editar_perfil', mensagem_sucesso=resultado_msg))
        else:
            return render_template('att_perfil.html', user=current_user, mensagem_erro=resultado_msg)

    return render_template(
        "att_perfil.html",
        user=current_user,
        mensagem_sucesso=request.args.get('mensagem_sucesso'),
        mensagem_erro=request.args.get('mensagem_erro')
    )

# -----------------
# AVALIAÇÃO
# -----------------

def ensure_avaliacao_header():
    if not os.path.exists(AVALIACAO_FILENAME) or os.path.getsize(AVALIACAO_FILENAME) == 0:
        with open(AVALIACAO_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['data_registro', 'nome', 'email', 'Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m'])

def atualizar_avaliacao(coluna, rating):
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
            'data_registro': data_registro, 'nome': current_user.nome, 'email': current_user.email,
            'Av_f': '', 'Av_s': '', 'Av_e': '', 'Av_a': '', 'Av_g': '', 'Av_m': ''
        }
        nova_linha[coluna] = rating
        rows.append(nova_linha)

    with open(AVALIACAO_FILENAME, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['data_registro','nome','email','Av_f','Av_s','Av_e','Av_a','Av_g','Av_m']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

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
# MEDIA AVALIAÇÃO
# -----------------------

def calcular_medias_por_categoria():
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
                            pontuacao = int(pontuacao_str)
                            dados_por_categoria[coluna]['soma'] += pontuacao
                            dados_por_categoria[coluna]['total'] += 1
                        except ValueError:
                            continue

            resultados_finais = {}
            for coluna, dados in dados_por_categoria.items():
                soma = dados['soma']
                total = dados['total']

                media = round(soma / total, 1) if total > 0 else 0.0

                resultados_finais[coluna] = {'media': media, 'total': total}

            return resultados_finais

    except IOError:
        return {col: {'media': 0.0, 'total': 0} for col in colunas_avaliacao}

# -----------------
# EXECUÇÃO
# -----------------

if __name__ == '__main__':
    ensure_avaliacao_header()
    app.run(debug=True)