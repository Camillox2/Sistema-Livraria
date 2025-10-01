"""
Sistema de Gerenciamento de Livraria - Web Version
Integrantes:
- Vitor Henrique Camillo
- Hiro Terato Ramos
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
import csv
import os
from pathlib import Path
from datetime import datetime
import shutil
import webbrowser
import threading

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configuração dos diretórios
BASE_DIR = Path("meu_sistema_livraria")
DATA_DIR = BASE_DIR / "data"
BACKUPS_DIR = BASE_DIR / "backups"
EXPORTS_DIR = BASE_DIR / "exports"
REPORTS_DIR = BASE_DIR / "reports"
UPLOAD_DIR = Path("uploads")
DB_PATH = DATA_DIR / "livraria.db"


def criar_estrutura():
    """Cria a estrutura de diretórios"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def inicializar_banco():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            ano_publicacao INTEGER NOT NULL,
            preco REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def fazer_backup():
    """Cria backup do banco de dados"""
    if not DB_PATH.exists():
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_nome = f"backup_livraria_{timestamp}.db"
    backup_path = BACKUPS_DIR / backup_nome

    shutil.copy2(DB_PATH, backup_path)
    limpar_backups_antigos()


def limpar_backups_antigos():
    """Mantém apenas os 5 backups mais recentes"""
    backups = sorted(BACKUPS_DIR.glob("backup_livraria_*.db"),
                    key=os.path.getmtime, reverse=True)

    for backup in backups[5:]:
        backup.unlink()


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/livros', methods=['GET'])
def listar_livros():
    """Lista todos os livros"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livros ORDER BY id')
    livros = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': l[0],
        'titulo': l[1],
        'autor': l[2],
        'ano_publicacao': l[3],
        'preco': l[4]
    } for l in livros])


@app.route('/api/livros', methods=['POST'])
def adicionar_livro():
    """Adiciona um novo livro"""
    try:
        dados = request.json
        titulo = dados['titulo']
        autor = dados['autor']
        ano_publicacao = int(dados['ano_publicacao'])
        preco = float(dados['preco'])

        # Validação
        if ano_publicacao < 0 or ano_publicacao > datetime.now().year:
            return jsonify({'erro': 'Ano de publicação inválido'}), 400

        if preco < 0:
            return jsonify({'erro': 'Preço não pode ser negativo'}), 400

        fazer_backup()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO livros (titulo, autor, ano_publicacao, preco)
            VALUES (?, ?, ?, ?)
        ''', (titulo, autor, ano_publicacao, preco))

        livro_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'id': livro_id,
            'titulo': titulo,
            'autor': autor,
            'ano_publicacao': ano_publicacao,
            'preco': preco,
            'mensagem': 'Livro adicionado com sucesso!'
        }), 201

    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@app.route('/api/livros/<int:id>', methods=['PUT'])
def atualizar_preco(id):
    """Atualiza o preço de um livro"""
    try:
        dados = request.json
        novo_preco = float(dados['preco'])

        if novo_preco < 0:
            return jsonify({'erro': 'Preço não pode ser negativo'}), 400

        fazer_backup()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM livros WHERE id = ?', (id,))
        livro = cursor.fetchone()

        if not livro:
            conn.close()
            return jsonify({'erro': 'Livro não encontrado'}), 404

        cursor.execute('UPDATE livros SET preco = ? WHERE id = ?', (novo_preco, id))
        conn.commit()
        conn.close()

        return jsonify({'mensagem': 'Preço atualizado com sucesso!'}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@app.route('/api/livros/<int:id>', methods=['DELETE'])
def remover_livro(id):
    """Remove um livro"""
    try:
        fazer_backup()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM livros WHERE id = ?', (id,))
        livro = cursor.fetchone()

        if not livro:
            conn.close()
            return jsonify({'erro': 'Livro não encontrado'}), 404

        cursor.execute('DELETE FROM livros WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        return jsonify({'mensagem': 'Livro removido com sucesso!'}), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@app.route('/api/livros/buscar/<autor>', methods=['GET'])
def buscar_por_autor(autor):
    """Busca livros por autor"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM livros
        WHERE autor LIKE ?
        ORDER BY titulo
    ''', (f'%{autor}%',))
    livros = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': l[0],
        'titulo': l[1],
        'autor': l[2],
        'ano_publicacao': l[3],
        'preco': l[4]
    } for l in livros])


@app.route('/api/exportar-csv', methods=['GET'])
def exportar_csv():
    """Exporta livros para CSV e retorna para download"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livros ORDER BY id')
    livros = cursor.fetchall()
    conn.close()

    if not livros:
        return jsonify({'erro': 'Nenhum livro para exportar'}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = f"livros_exportados_{timestamp}.csv"
    csv_path = EXPORTS_DIR / csv_filename

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Título', 'Autor', 'Ano de Publicação', 'Preço'])
        writer.writerows(livros)

    return send_file(csv_path, as_attachment=True, download_name=csv_filename, mimetype='text/csv')


@app.route('/api/backup', methods=['POST'])
def criar_backup():
    """Cria um backup manual"""
    fazer_backup()
    return jsonify({'mensagem': 'Backup criado com sucesso!'}), 200


@app.route('/api/backups', methods=['GET'])
def listar_backups():
    """Lista todos os backups disponíveis"""
    backups = sorted(BACKUPS_DIR.glob("backup_livraria_*.db"),
                    key=os.path.getmtime, reverse=True)

    return jsonify([{
        'nome': b.name,
        'data': datetime.fromtimestamp(os.path.getmtime(b)).strftime('%d/%m/%Y %H:%M:%S'),
        'tamanho': f"{os.path.getsize(b) / 1024:.2f} KB"
    } for b in backups])


@app.route('/api/importar-csv', methods=['POST'])
def importar_csv():
    """Importa livros de um arquivo CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'erro': 'Nenhum arquivo selecionado'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'erro': 'Apenas arquivos CSV são permitidos'}), 400

        # Salva o arquivo temporariamente
        filename = secure_filename(file.filename)
        filepath = UPLOAD_DIR / filename
        file.save(filepath)

        # Faz backup antes de importar
        fazer_backup()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        importados = 0
        erros = []

        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Pula o cabeçalho

            for idx, row in enumerate(reader, start=2):
                if len(row) >= 5:
                    try:
                        # Ignora o ID do CSV
                        _, titulo, autor, ano, preco = row
                        ano = int(ano)
                        preco = float(preco)

                        # Validação
                        if ano < 0 or ano > datetime.now().year:
                            erros.append(f"Linha {idx}: Ano inválido ({ano})")
                            continue

                        if preco < 0:
                            erros.append(f"Linha {idx}: Preço inválido ({preco})")
                            continue

                        cursor.execute('''
                            INSERT INTO livros (titulo, autor, ano_publicacao, preco)
                            VALUES (?, ?, ?, ?)
                        ''', (titulo, autor, ano, preco))

                        importados += 1
                    except (ValueError, sqlite3.Error) as e:
                        erros.append(f"Linha {idx}: {str(e)}")

        conn.commit()
        conn.close()

        # Remove o arquivo temporário
        filepath.unlink()

        resultado = {
            'mensagem': f'{importados} livro(s) importado(s) com sucesso!',
            'importados': importados,
            'erros': erros
        }

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 400


@app.route('/api/relatorio-html', methods=['GET'])
def gerar_relatorio_html():
    """Gera relatório em HTML"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM livros ORDER BY titulo')
    livros = cursor.fetchall()
    conn.close()

    if not livros:
        return jsonify({'erro': 'Nenhum livro para gerar relatório'}), 400

    # Calcula estatísticas
    total_livros = len(livros)
    autores_unicos = len(set(l[2] for l in livros))
    valor_total = sum(l[4] for l in livros)
    preco_medio = valor_total / total_livros

    # Gera HTML
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Livraria</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 1em;
            opacity: 0.9;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 0.9em;
        }}
        .preco {{
            color: #27ae60;
            font-weight: bold;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Relatório de Livraria</h1>
        <div class="subtitle">Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_livros}</div>
                <div class="stat-label">Total de Livros</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{autores_unicos}</div>
                <div class="stat-label">Autores Únicos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">R$ {valor_total:.2f}</div>
                <div class="stat-label">Valor Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">R$ {preco_medio:.2f}</div>
                <div class="stat-label">Preço Médio</div>
            </div>
        </div>

        <h2 style="color: #667eea; margin-top: 40px;">Catálogo Completo</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Título</th>
                    <th>Autor</th>
                    <th>Ano</th>
                    <th>Preço</th>
                </tr>
            </thead>
            <tbody>
"""

    for livro in livros:
        html += f"""
                <tr>
                    <td>{livro[0]}</td>
                    <td>{livro[1]}</td>
                    <td>{livro[2]}</td>
                    <td>{livro[3]}</td>
                    <td class="preco">R$ {livro[4]:.2f}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>

        <div class="footer">
            <p><strong>Desenvolvido por:</strong> Vitor Henrique Camillo & Hiro Terato Ramos</p>
            <p>Sistema de Gerenciamento de Livraria © 2025</p>
        </div>
    </div>
</body>
</html>
"""

    # Salva o relatório
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORTS_DIR / f"relatorio_{timestamp}.html"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return send_file(report_path, as_attachment=True, download_name=f'relatorio_livraria_{timestamp}.html')


@app.route('/api/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Retorna estatísticas para gráficos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Livros por autor
    cursor.execute('''
        SELECT autor, COUNT(*) as total
        FROM livros
        GROUP BY autor
        ORDER BY total DESC
        LIMIT 10
    ''')
    livros_por_autor = [{'autor': row[0], 'total': row[1]} for row in cursor.fetchall()]

    # Livros por década
    cursor.execute('''
        SELECT (ano_publicacao / 10) * 10 as decada, COUNT(*) as total
        FROM livros
        GROUP BY decada
        ORDER BY decada
    ''')
    livros_por_decada = [{'decada': f"{int(row[0])}s", 'total': row[1]} for row in cursor.fetchall()]

    # Distribuição de preços
    cursor.execute('''
        SELECT
            CASE
                WHEN preco < 20 THEN 'Até R$ 20'
                WHEN preco < 50 THEN 'R$ 20-50'
                WHEN preco < 100 THEN 'R$ 50-100'
                ELSE 'Acima de R$ 100'
            END as faixa,
            COUNT(*) as total
        FROM livros
        GROUP BY faixa
    ''')
    distribuicao_precos = [{'faixa': row[0], 'total': row[1]} for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'livros_por_autor': livros_por_autor,
        'livros_por_decada': livros_por_decada,
        'distribuicao_precos': distribuicao_precos
    })


def abrir_navegador():
    """Abre o navegador automaticamente"""
    webbrowser.open('http://127.0.0.1:5000')


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SISTEMA DE GERENCIAMENTO DE LIVRARIA - WEB")
    print("="*60)
    print("\nIntegrantes:")
    print("  - Vitor Henrique Camillo")
    print("  - Hiro Terato Ramos")
    print("="*60)
    print("\n🚀 Iniciando servidor...")
    print("📱 Abrindo navegador em: http://127.0.0.1:5000")
    print("\n💡 Para encerrar: pressione Ctrl+C")
    print("="*60 + "\n")

    criar_estrutura()
    inicializar_banco()

    # Abre o navegador após 1.5 segundos
    threading.Timer(1.5, abrir_navegador).start()

    app.run(debug=True, use_reloader=False)
