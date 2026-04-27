# WAN — Plataforma Terapêutica para Crianças com TEA

Plataforma web de apoio terapêutico desenvolvida como Trabalho de Conclusão de Curso (TCC). O sistema auxilia psicólogos no ensino e acompanhamento do reconhecimento de emoções em crianças com Transtorno do Espectro Autista (TEA).

---

## Sobre o projeto

A atividade principal consiste em apresentar imagens de expressões faciais à criança e perguntar, por exemplo, *"Quem está feliz?"*. A criança escolhe a imagem correta e o sistema registra o resultado — acerto, erro e tempo de resposta — permitindo que o psicólogo acompanhe a evolução ao longo do tempo.

### Perfis de usuário

| Perfil | Responsabilidades |
|---|---|
| **Administrador** | Gerencia usuários e aprova cadastros de psicólogos |
| **Psicólogo** | Cadastra crianças, cria atividades e sessões, acompanha desempenho |
| **Responsável** | Visualiza o progresso, executa atividades junto com a criança |
| **Criança** | Não possui login — sempre mediada por um adulto |

### Módulos

- **accounts** — Autenticação e perfis de usuário (Admin, Psicólogo, Responsável)
- **criancas** — Cadastro e gestão de crianças vinculadas a psicólogo e responsáveis
- **atividades** — Atividades de identificação de emoções com imagens rotuladas
- **sessoes** — Sessões terapêuticas que agrupam atividades e crianças
- **desempenho** — Registro de resultados por criança, atividade e sessão

### Stack

- **Backend:** Python 3 + Django 5.2
- **Frontend:** HTML, CSS e JavaScript puro (sem frameworks JS)
- **Banco de dados:** SQLite (desenvolvimento)
- **Upload de imagens:** Pillow

---

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Passo a passo

**1. Clone o repositório**

```bash
git clone <url-do-repositorio>
cd "TCC WAN"
```

**2. Crie e ative o ambiente virtual**

```bash
# Criar
python -m venv venv

# Ativar — Windows
venv\Scripts\activate

# Ativar — Linux/macOS
source venv/bin/activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Aplique as migrações**

```bash
python manage.py migrate
```

**5. Crie um superusuário (Administrador)**

```bash
python manage.py createsuperuser
```

**6. Inicie o servidor**

```bash
python manage.py runserver
```

O sistema estará disponível em `http://127.0.0.1:8000`.

---

## Estrutura de pastas

```
TCC WAN/
├── accounts/       # Usuários e autenticação
├── atividades/     # Atividades e imagens de emoções
├── criancas/       # Perfis de crianças
├── sessoes/        # Sessões terapêuticas
├── desempenho/     # Registro de resultados
├── core/           # Configurações principais do projeto
├── templates/      # Templates HTML
├── static/         # Arquivos estáticos (CSS, JS, imagens)
├── media/          # Uploads (fotos, imagens de emoções)
├── manage.py
└── requirements.txt
```
