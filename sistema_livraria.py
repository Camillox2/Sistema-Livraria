"""
Sistema de Gerenciamento de Livraria
Integrantes:
- Vitor Henrique Camillo
- Hiro Terato Ramos

Este sistema gerencia uma livraria utilizando SQLite para banco de dados,
manipulação de arquivos CSV para importação/exportação, e sistema de backup automático.
"""

import sqlite3
import csv
import os
from pathlib import Path
from datetime import datetime
import shutil


class SistemaLivraria:
    """Classe principal para gerenciar o sistema de livraria"""

    def __init__(self):
        """Inicializa o sistema e cria a estrutura de diretórios"""
        self.base_dir = Path("meu_sistema_livraria")
        self.data_dir = self.base_dir / "data"
        self.backups_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.db_path = self.data_dir / "livraria.db"

        self._criar_estrutura_diretorios()
        self._inicializar_banco()

    def _criar_estrutura_diretorios(self):
        """Cria a estrutura de diretórios necessária"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        print("✓ Estrutura de diretórios criada/verificada")

    def _inicializar_banco(self):
        """Cria a tabela de livros se não existir"""
        conn = sqlite3.connect(self.db_path)
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
        print("✓ Banco de dados inicializado")

    def _fazer_backup(self):
        """Cria um backup do banco de dados com timestamp"""
        if not self.db_path.exists():
            print("⚠ Banco de dados não encontrado para backup")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_nome = f"backup_livraria_{timestamp}.db"
        backup_path = self.backups_dir / backup_nome

        shutil.copy2(self.db_path, backup_path)
        print(f"✓ Backup criado: {backup_nome}")

        self._limpar_backups_antigos()

    def _limpar_backups_antigos(self):
        """Mantém apenas os 5 backups mais recentes"""
        backups = sorted(self.backups_dir.glob("backup_livraria_*.db"),
                        key=os.path.getmtime, reverse=True)

        # Remove backups excedentes (mantém apenas os 5 mais recentes)
        for backup in backups[5:]:
            backup.unlink()
            print(f"✓ Backup antigo removido: {backup.name}")

    def adicionar_livro(self, titulo, autor, ano_publicacao, preco):
        """Adiciona um novo livro ao banco de dados"""
        # Validação de entradas
        try:
            ano_publicacao = int(ano_publicacao)
            preco = float(preco)

            if ano_publicacao < 0 or ano_publicacao > datetime.now().year:
                print("✗ Ano de publicação inválido")
                return False

            if preco < 0:
                print("✗ Preço não pode ser negativo")
                return False

        except ValueError:
            print("✗ Ano ou preço inválido")
            return False

        self._fazer_backup()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO livros (titulo, autor, ano_publicacao, preco)
            VALUES (?, ?, ?, ?)
        ''', (titulo, autor, ano_publicacao, preco))

        conn.commit()
        conn.close()

        print(f"✓ Livro '{titulo}' adicionado com sucesso!")
        return True

    def exibir_todos_livros(self):
        """Exibe todos os livros cadastrados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM livros ORDER BY id')
        livros = cursor.fetchall()

        conn.close()

        if not livros:
            print("\nNenhum livro cadastrado.")
            return

        print("\n" + "="*100)
        print(f"{'ID':<5} {'Título':<35} {'Autor':<25} {'Ano':<6} {'Preço':<10}")
        print("="*100)

        for livro in livros:
            id_livro, titulo, autor, ano, preco = livro
            print(f"{id_livro:<5} {titulo:<35} {autor:<25} {ano:<6} R$ {preco:<8.2f}")

        print("="*100)
        print(f"Total de livros: {len(livros)}\n")

    def atualizar_preco(self, id_livro, novo_preco):
        """Atualiza o preço de um livro"""
        try:
            novo_preco = float(novo_preco)
            if novo_preco < 0:
                print("✗ Preço não pode ser negativo")
                return False
        except ValueError:
            print("✗ Preço inválido")
            return False

        self._fazer_backup()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT titulo FROM livros WHERE id = ?', (id_livro,))
        resultado = cursor.fetchone()

        if not resultado:
            print(f"✗ Livro com ID {id_livro} não encontrado")
            conn.close()
            return False

        cursor.execute('UPDATE livros SET preco = ? WHERE id = ?', (novo_preco, id_livro))
        conn.commit()
        conn.close()

        print(f"✓ Preço do livro '{resultado[0]}' atualizado para R$ {novo_preco:.2f}")
        return True

    def remover_livro(self, id_livro):
        """Remove um livro do banco de dados"""
        self._fazer_backup()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT titulo FROM livros WHERE id = ?', (id_livro,))
        resultado = cursor.fetchone()

        if not resultado:
            print(f"✗ Livro com ID {id_livro} não encontrado")
            conn.close()
            return False

        cursor.execute('DELETE FROM livros WHERE id = ?', (id_livro,))
        conn.commit()
        conn.close()

        print(f"✓ Livro '{resultado[0]}' removido com sucesso!")
        return True

    def buscar_por_autor(self, autor):
        """Busca livros por autor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM livros
            WHERE autor LIKE ?
            ORDER BY titulo
        ''', (f'%{autor}%',))

        livros = cursor.fetchall()
        conn.close()

        if not livros:
            print(f"\nNenhum livro encontrado para o autor '{autor}'.")
            return

        print(f"\n{'='*100}")
        print(f"Livros do autor '{autor}':")
        print(f"{'='*100}")
        print(f"{'ID':<5} {'Título':<35} {'Autor':<25} {'Ano':<6} {'Preço':<10}")
        print("="*100)

        for livro in livros:
            id_livro, titulo, autor_nome, ano, preco = livro
            print(f"{id_livro:<5} {titulo:<35} {autor_nome:<25} {ano:<6} R$ {preco:<8.2f}")

        print("="*100)
        print(f"Total encontrado: {len(livros)}\n")

    def exportar_para_csv(self):
        """Exporta todos os livros para um arquivo CSV"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM livros ORDER BY id')
        livros = cursor.fetchall()

        conn.close()

        if not livros:
            print("✗ Nenhum livro para exportar")
            return False

        csv_path = self.exports_dir / "livros_exportados.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Título', 'Autor', 'Ano de Publicação', 'Preço'])
            writer.writerows(livros)

        print(f"✓ {len(livros)} livro(s) exportado(s) para: {csv_path}")
        return True

    def importar_de_csv(self, caminho_csv=None):
        """Importa livros de um arquivo CSV"""
        if caminho_csv is None:
            caminho_csv = self.exports_dir / "livros_exportados.csv"
        else:
            caminho_csv = Path(caminho_csv)

        if not caminho_csv.exists():
            print(f"✗ Arquivo CSV não encontrado: {caminho_csv}")
            return False

        self._fazer_backup()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        importados = 0
        with open(caminho_csv, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Pula o cabeçalho

            for row in reader:
                if len(row) >= 5:
                    try:
                        # Ignora o ID do CSV e deixa o banco gerar automaticamente
                        _, titulo, autor, ano, preco = row
                        ano = int(ano)
                        preco = float(preco)

                        cursor.execute('''
                            INSERT INTO livros (titulo, autor, ano_publicacao, preco)
                            VALUES (?, ?, ?, ?)
                        ''', (titulo, autor, ano, preco))

                        importados += 1
                    except (ValueError, sqlite3.Error) as e:
                        print(f"⚠ Erro ao importar linha {row}: {e}")

        conn.commit()
        conn.close()

        print(f"✓ {importados} livro(s) importado(s) com sucesso!")
        return True

    def menu_principal(self):
        """Exibe e gerencia o menu principal do sistema"""
        while True:
            print("\n" + "="*50)
            print("    SISTEMA DE GERENCIAMENTO DE LIVRARIA")
            print("="*50)
            print("1. Adicionar novo livro")
            print("2. Exibir todos os livros")
            print("3. Atualizar preço de um livro")
            print("4. Remover um livro")
            print("5. Buscar livros por autor")
            print("6. Exportar dados para CSV")
            print("7. Importar dados de CSV")
            print("8. Fazer backup do banco de dados")
            print("9. Sair")
            print("="*50)

            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                print("\n--- ADICIONAR NOVO LIVRO ---")
                titulo = input("Título: ").strip()
                autor = input("Autor: ").strip()
                ano = input("Ano de publicação: ").strip()
                preco = input("Preço (R$): ").strip()

                if titulo and autor and ano and preco:
                    self.adicionar_livro(titulo, autor, ano, preco)
                else:
                    print("✗ Todos os campos são obrigatórios")

            elif opcao == '2':
                self.exibir_todos_livros()

            elif opcao == '3':
                print("\n--- ATUALIZAR PREÇO ---")
                id_livro = input("ID do livro: ").strip()
                novo_preco = input("Novo preço (R$): ").strip()

                if id_livro and novo_preco:
                    self.atualizar_preco(id_livro, novo_preco)
                else:
                    print("✗ ID e preço são obrigatórios")

            elif opcao == '4':
                print("\n--- REMOVER LIVRO ---")
                id_livro = input("ID do livro: ").strip()

                if id_livro:
                    confirma = input(f"Confirma a remoção do livro ID {id_livro}? (s/n): ").strip().lower()
                    if confirma == 's':
                        self.remover_livro(id_livro)
                else:
                    print("✗ ID é obrigatório")

            elif opcao == '5':
                print("\n--- BUSCAR POR AUTOR ---")
                autor = input("Nome do autor: ").strip()

                if autor:
                    self.buscar_por_autor(autor)
                else:
                    print("✗ Nome do autor é obrigatório")

            elif opcao == '6':
                print("\n--- EXPORTAR PARA CSV ---")
                self.exportar_para_csv()

            elif opcao == '7':
                print("\n--- IMPORTAR DE CSV ---")
                caminho = input("Caminho do arquivo CSV (Enter para padrão): ").strip()
                self.importar_de_csv(caminho if caminho else None)

            elif opcao == '8':
                print("\n--- FAZER BACKUP ---")
                self._fazer_backup()

            elif opcao == '9':
                print("\n✓ Encerrando o sistema...")
                break

            else:
                print("\n✗ Opção inválida! Escolha uma opção de 1 a 9.")


def main():
    """Função principal que inicia o sistema"""
    print("\n" + "="*50)
    print("  Iniciando Sistema de Gerenciamento de Livraria")
    print("="*50)
    print("\nIntegrantes:")
    print("  - Vitor Henrique Camillo")
    print("  - Hiro Terato Ramos")
    print("="*50 + "\n")

    sistema = SistemaLivraria()
    sistema.menu_principal()


if __name__ == "__main__":
    main()
