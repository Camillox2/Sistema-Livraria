# 📚 Sistema de Gerenciamento de Livraria - Web

**Integrantes:**
- Vitor Henrique Camillo
- Hiro Terato Ramos

## 🚀 Como Executar

### 1. Instalar as dependências:
```bash
pip install -r requirements.txt
```

### 2. Executar o sistema:
```bash
python app.py
```

O sistema abrirá automaticamente no seu navegador em: `http://127.0.0.1:5000`

## ✨ Funcionalidades

### Backend (Flask + SQLite)
- ✅ Banco de dados SQLite com tabela de livros
- ✅ API REST completa (CRUD)
- ✅ Sistema de backup automático
- ✅ Exportação para CSV
- ✅ Validação de dados
- ✅ Limpeza automática de backups (mantém apenas os 5 mais recentes)

### Frontend (HTML/CSS/JavaScript)
- ✅ Interface moderna e responsiva
- ✅ Design com gradientes e animações
- ✅ Cards de livros com hover effects
- ✅ Painel de estatísticas (total de livros, autores, valor total)
- ✅ Busca por autor em tempo real
- ✅ Notificações visuais de sucesso/erro
- ✅ Modal para edição de preços
- ✅ Grid responsivo que se adapta a diferentes telas

## 📁 Estrutura de Arquivos

```
E:\pyton\
├── app.py                          # Backend Flask
├── templates/
│   └── index.html                  # Frontend
├── requirements.txt                # Dependências
└── meu_sistema_livraria/           # Criado automaticamente
    ├── data/
    │   └── livraria.db             # Banco de dados
    ├── backups/
    │   └── backup_livraria_*.db    # Backups automáticos
    └── exports/
        └── livros_exportados.csv   # Exportações CSV
```

## 🎨 Características do Design

- Paleta de cores roxa/azul moderna
- Animações suaves em todos os elementos
- Cards com efeito de elevação ao passar o mouse
- Notificações deslizantes
- Interface totalmente responsiva
- Ícones emoji para melhor UX

## 🔧 Tecnologias Utilizadas

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Bibliotecas:** flask-cors, pathlib, datetime
