import os
import csv
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# --------------------------------------------------------------------------------------
# 1. CONFIGURAÇÕES INICIAIS DA APLICAÇÃO
# --------------------------------------------------------------------------------------

# Configuração da aplicação Flask
app = Flask(__name__)
# Chave secreta para segurança da sessão (MUITO importante)
app.secret_key = 'uma_chave_secreta_muito_forte_e_dificil' 

# Configurações de diretórios e arquivos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
CSV_FILENAME = 'usuarios.csv'
AVALIACAO_FILENAME = 'avaliacao.csv'
DEFAULT_PHOTO_PATH = 'img/user-default.png' # Caminho relativo à pasta static

# Cria a pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Variável global em memória para armazenar os usuários
USERS = {} 

# --- Inicializa o Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'formulario_login' # Define a rota de login

# --------------------------------------------------------------------------------------
# 2. UTILITÁRIOS DE ARQUIVO CSV
# (Funções de baixo nível para garantir a integridade dos arquivos)
# --------------------------------------------------------------------------------------

def ensure_csv_header(filename, fieldnames):
    """Garante que um arquivo CSV exista e tenha o cabeçalho correto, criando-o se necessário."""
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(fieldnames)

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida para upload."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --------------------------------------------------------------------------------------
# 3. ROTAS DE NAVEGAÇÃO E AULAS (GET)
# (Acesso público e páginas de cursos protegidas por login)
# --------------------------------------------------------------------------------------

@app.route('/')
def home():
    """Rota da página inicial."""
    return render_template('index.html', user=current_user)

@app.route('/FAQ')
def FAQ():
    """Rota da página de Perguntas Frequentes."""
    return render_template('FAQ.html', user=current_user)

@app.route('/pagcursos')
@login_required 
def pagcursos():
    """Rota da página principal de cursos, protegida por login."""
    return render_template('pagcursos.html', user=current_user)

@app.route('/media_avaliacoes')
@login_required
def media_avaliacoes():
    """Renderiza a página que exibe todas as médias de avaliação dos módulos."""
    # Chama a função de cálculo que está no Bloco 7
    medias_completas = calcular_medias_por_categoria()
    return render_template('media_avaliacoes.html', 
                           user=current_user, 
                           medias=medias_completas)

# Função auxiliar para buscar dados de média (utiliza a função do Bloco 7)
def get_media_data(module_key):
    """Busca a média de um módulo específico."""
    medias = calcular_medias_por_categoria()
    return medias.get(module_key, {'media': 0, 'total': 0})

@app.route('/fração-class')
@login_required
def aula_fra():
    media_data = get_media_data('Av_f')
    return render_template('fracao-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])

@app.route('/sistemanumeracao-class')
@login_required
def aula_sisenum():
    media_data = get_media_data('Av_s')
    return render_template('sistemanumeracao-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])

@app.route('/equacao1grau-class')
@login_required
def aula_1_equa():
    media_data = get_media_data('Av_e')
    return render_template('equacao1grau-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])

@app.route('/angulo-class')
@login_required
def aula_ang():
    media_data = get_media_data('Av_a')
    return render_template('angulo-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])

@app.route('/geometria-class')
@login_required
def aula_geom():
    media_data = get_media_data('Av_g')
    return render_template('geometria-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])

@app.route('/mult_e_div-class')
@login_required
def aula_mult_e_div():
    media_data = get_media_data('Av_m') 
    return render_template('mult_e_div-class.html', user=current_user, media=media_data['media'], total_avaliacoes=media_data['total'])


# --------------------------------------------------------------------------------------
# 4. MODELO DO USUÁRIO E UTILITÁRIOS
# (Estrutura de dados, busca e carregamento inicial)
# --------------------------------------------------------------------------------------

class User(UserMixin):
    """Modelo de usuário para Flask-Login."""
    def __init__(self, id, nome, email, password, foto_perfil=DEFAULT_PHOTO_PATH):
        self.id = id
        self.nome = nome
        self.email = email
        self.password = password
        self.foto_perfil = foto_perfil

    def get_id(self):
        """Retorna o ID do usuário para o Flask-Login."""
        return str(self.id)

# --- Funções Auxiliares de Gerenciamento de Usuário ---

def find_user_by_email(email):
    """Busca um usuário no dicionário USERS pelo email."""
    for user_id, user in USERS.items():
        if user.email.lower() == email.lower():
            return user
    return None

def update_user_in_csv(target_user, new_data):
    """
    Atualiza um usuário no CSV com novos dados e recarrega a lista USERS.
    Usado no Bloco 6 (Atualização de Perfil).
    """
    rows = []
    found = False
    
    # 1. Leitura e Modificação em memória
    with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
        fieldnames = ['data_registro', 'nome', 'email', 'senha', 'foto_perfil']
        reader = csv.DictReader(file, fieldnames=fieldnames)
        try:
            next(reader) # Pula o cabeçalho
        except StopIteration:
            pass 
        
        for row in reader:
            if row['email'].lower() == target_user.email.lower():
                # Aplica as modificações
                row['nome'] = new_data.get('nome', row['nome'])
                row['email'] = new_data.get('email', row['email'])
                row['senha'] = new_data.get('senha', row['senha'])
                row['foto_perfil'] = new_data.get('foto_perfil', row['foto_perfil'])
                found = True
            rows.append(row)
    
    if not found:
        return False
        
    # 2. Reescreve todo o arquivo
    fieldnames = ['data_registro', 'nome', 'email', 'senha', 'foto_perfil']
    with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    # 3. Recarrega a lista USERS para refletir a mudança no app
    load_initial_users_from_csv()
    return True

# --- Carregamento Inicial e User Loader (Obrigações do Flask-Login) ---

@login_manager.user_loader
def load_user(user_id):
    """O Flask-Login usa esta função para carregar o objeto User pelo ID da sessão."""
    return USERS.get(user_id)

def load_initial_users_from_csv():
    """Carrega todos os usuários do CSV para a memória (variável USERS) no início e após updates."""
    global USERS
    USERS.clear()
    fieldnames = ['data_registro', 'nome', 'email', 'senha', 'foto_perfil']
    ensure_csv_header(CSV_FILENAME, fieldnames)
    
    if os.path.exists(CSV_FILENAME):
        try:
            with open(CSV_FILENAME, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader, None) # Pula o cabeçalho
                for i, row in enumerate(reader, start=1):
                    if len(row) < 4: continue 
                    data_registro, nome, email, senha = row[0:4]
                    foto_perfil = row[4] if len(row) > 4 and row[4] else DEFAULT_PHOTO_PATH
                    
                    user_id = str(i)
                    USERS[user_id] = User(user_id, nome, email, senha, foto_perfil)
        except Exception as e:
            print(f"AVISO: Não foi possível ler o CSV de usuários: {e}")

# Carrega os usuários na inicialização do app (Chama a função)
load_initial_users_from_csv()


# --------------------------------------------------------------------------------------
# 5. CADASTRO DE USUÁRIO
# (Rota para criar um novo usuário e salvar no CSV)
# --------------------------------------------------------------------------------------

@app.route('/salvar_dados', methods=['POST'])
def salvar_dados():
    """CADASTRO: Rota para criar um novo usuário e salvar no CSV."""
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    confirm_senha = request.form.get('confirm_senha')
    data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if senha != confirm_senha:
        flash('As senhas não coincidem. Tente novamente.')
        return redirect(url_for('home'))

    if find_user_by_email(email):
        flash('Este email já está cadastrado. Tente fazer login.')
        return redirect(url_for('home'))

    # Hash da senha para segurança
    hashed_password = generate_password_hash(senha)
    
    # Adiciona o novo usuário ao CSV
    fieldnames = ['data_registro', 'nome', 'email', 'senha', 'foto_perfil']
    ensure_csv_header(CSV_FILENAME, fieldnames) # Garante que o arquivo e cabeçalho existam
    with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([data_registro, nome, email, hashed_password, DEFAULT_PHOTO_PATH])
        
    # Recarrega a lista global de usuários para incluir o novo registro
    load_initial_users_from_csv()
    
    flash('Cadastro realizado com sucesso! Faça login para continuar.')
    return redirect(url_for('home'))


# --------------------------------------------------------------------------------------
# 6. LOGIN E GESTÃO DE SESSÃO
# (Rotas para autenticar, iniciar e encerrar a sessão)
# --------------------------------------------------------------------------------------

@app.route('/formulario_login', methods=['GET', 'POST'])
def formulario_login():
    """LOGIN: Rota para receber credenciais, autenticar e iniciar a sessão."""
    if current_user.is_authenticated:
        return redirect(url_for('pagcursos'))

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        user_found = find_user_by_email(email)

        if user_found and check_password_hash(user_found.password, senha):
            # Login bem-sucedido: verifica o hash da senha
            login_user(user_found) # Inicia a sessão com o Flask-Login
            flash('Login realizado com sucesso!')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('pagcursos'))
        
        # Falha no login
        flash('E-mail ou senha incorretos.')
    
    return render_template('index.html', user=current_user) 


@app.route('/logout')
@login_required
def logout():
    """LOGOUT: Encerra a sessão do usuário logado."""
    logout_user()
    flash('Você foi desconectado com sucesso.')
    return redirect(url_for('home'))


# --------------------------------------------------------------------------------------
# 7. ATUALIZAÇÃO DO PERFIL (EDIÇÃO DE DADOS E FOTO)
# (Lógica para o usuário alterar seus dados e persistir as mudanças no CSV)
# --------------------------------------------------------------------------------------

def handle_profile_picture_upload(file, current_user_foto_path):
    """Salva a nova foto e retorna o novo caminho, deletando a foto antiga se necessário."""
    
    # Verifica se a foto antiga não é a padrão e tenta deletá-la
    if current_user_foto_path != DEFAULT_PHOTO_PATH:
        try:
            old_path = os.path.join(app.root_path, 'static', current_user_foto_path)
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception as e:
            print(f"Erro ao deletar foto antiga: {e}")

    # Salva o novo arquivo
    filename = f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Retorna o caminho relativo para o CSV e o objeto User
    return os.path.join(os.path.basename(app.config['UPLOAD_FOLDER']), filename).replace('\\', '/')

@app.route('/editar_perfil')
@login_required
def editar_perfil():
    """Renderiza a página de edição de perfil."""
    return render_template('editar_perfil.html', user=current_user)

@app.route('/atualizap', methods=['POST'])
@login_required
def atualizap():
    """Processa o formulário de atualização de perfil (POST)."""
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    file = request.files.get('file_foto')
    
    # 1. Validação da Senha Atual (Obrigatório para segurança)
    if not check_password_hash(current_user.password, senha_atual):
        flash('A senha atual fornecida está incorreta.')
        return redirect(url_for('editar_perfil'))

    # Dicionário para armazenar as mudanças
    new_data = {
        'data_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'nome': nome,
        'email': email,
        'senha': current_user.password, 
        'foto_perfil': current_user.foto_perfil
    }

    # 2. Processa a Nova Senha
    if nova_senha:
        new_data['senha'] = generate_password_hash(nova_senha)

    # 3. Processa o Upload da Foto
    if file and allowed_file(file.filename):
        new_photo_path = handle_profile_picture_upload(file, current_user.foto_perfil)
        new_data['foto_perfil'] = new_photo_path
    
    # 4. Atualiza o CSV e recarrega a lista USERS (utiliza função do Bloco 4)
    if update_user_in_csv(current_user, new_data):
        # Re-loga o usuário com a nova instância atualizada
        updated_user = find_user_by_email(email)
        if updated_user:
            login_user(updated_user)
            flash('Perfil atualizado com sucesso!')
        else:
            flash('Erro ao recarregar o perfil após a atualização.', 'error')
            logout_user()
            return redirect(url_for('home'))
    else:
        flash('Erro ao salvar as alterações no arquivo.', 'error')
    
    return redirect(url_for('editar_perfil'))


# --------------------------------------------------------------------------------------
# 8. AVALIAÇÃO E MÉDIA
# (Tudo sobre salvar e calcular as notas dos módulos)
# --------------------------------------------------------------------------------------

# --- Funções Auxiliares de Avaliação ---

def ensure_avaliacao_header():
    """Garante que o arquivo de avaliações exista e tenha o cabeçalho correto."""
    fieldnames = ['data_registro', 'nome', 'email', 'Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m']
    ensure_csv_header(AVALIACAO_FILENAME, fieldnames)

def atualizar_avaliacao(coluna, rating):
    """Lê o CSV, atualiza a nota do usuário logado para a coluna/módulo e reescreve o arquivo."""
    data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ensure_avaliacao_header()

    rows = []
    updated = False
    fieldnames = ['data_registro', 'nome', 'email', 'Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m']

    # 1. Leitura e Modificação em memória
    try:
        with open(AVALIACAO_FILENAME, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['email'].lower() == current_user.email.lower():
                    row[coluna] = rating
                    row['data_registro'] = data_registro
                    updated = True
                rows.append(row)
    except Exception as e:
        print(f"Erro na leitura do CSV de avaliação: {e}")

    # 2. Criação de nova linha
    if not updated:
        nova_linha = {fn: '' for fn in fieldnames} 
        nova_linha.update({
            'data_registro': data_registro, 
            'nome': current_user.nome, 
            'email': current_user.email,
            coluna: rating
        })
        rows.append(nova_linha)

    # 3. Reescreve todo o arquivo
    try:
        with open(AVALIACAO_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        print(f"Erro na escrita do CSV de avaliação: {e}")
        
def calcular_medias_por_categoria():
    """Calcula a média de avaliação e o total de votos para cada módulo."""
    ensure_avaliacao_header()
    modulos = {key: {'soma': 0, 'total': 0} for key in ['Av_f', 'Av_s', 'Av_e', 'Av_a', 'Av_g', 'Av_m']}
    
    try:
        with open(AVALIACAO_FILENAME, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                for key in modulos.keys():
                    rating_str = row.get(key)
                    if rating_str and rating_str.isdigit():
                        rating = int(rating_str)
                        if 1 <= rating <= 5: 
                            modulos[key]['soma'] += rating
                            modulos[key]['total'] += 1
    except Exception as e:
        print(f"Erro ao calcular médias: {e}")

    # Calcula a média final
    resultado = {}
    for key, data in modulos.items():
        media = data['soma'] / data['total'] if data['total'] > 0 else 0
        resultado[key] = {'media': round(media, 1), 'total': data['total']}
        
    return resultado


# --- Rotas de Submissão de Avaliação ---

@app.route('/avaliar_fra', methods=['POST'])
@login_required
def avaliar_fra():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_f', rating)
    flash('Avaliação de Fração registrada!')
    return redirect(url_for('aula_fra'))

@app.route('/avaliar_sisenum', methods=['POST'])
@login_required
def avaliar_sisenum():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_s', rating)
    flash('Avaliação de Sistema de Numeração registrada!')
    return redirect(url_for('aula_sisenum'))

@app.route('/avaliar_1grau', methods=['POST'])
@login_required
def avaliar_1grau():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_e', rating)
    flash('Avaliação de Equação de 1º Grau registrada!')
    return redirect(url_for('aula_1_equa'))

@app.route('/avaliar_ang', methods=['POST'])
@login_required
def avaliar_ang():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_a', rating)
    flash('Avaliação de Ângulos registrada!')
    return redirect(url_for('aula_ang'))

@app.route('/avaliar_geom', methods=['POST'])
@login_required
def avaliar_geom():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_g', rating)
    flash('Avaliação de Geometria registrada!')
    return redirect(url_for('aula_geom'))

@app.route('/avaliar_mult_div', methods=['POST'])
@login_required
def avaliar_mult_div():
    rating = request.form.get('rating')
    atualizar_avaliacao('Av_m', rating)
    flash('Avaliação de Múltiplos e Divisores registrada!')
    return redirect(url_for('aula_mult_e_div'))


# --------------------------------------------------------------------------------------
# 9. EXECUÇÃO DO SERVIDOR
# --------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)