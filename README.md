# 🎓 Mercado em Conexão (UFMG) — Pesquisa de Demanda & Torneio Gamificado (Bradley-Terry / Elo)

Plataforma oficial desenvolvida em **Python** (**FastAPI**), **SQLite** e interface moderna responsiva para a **Mercado em Conexão (Feira de Carreiras da UFMG)**. O sistema integra a **Pesquisa de Demanda e Preferências dos Estudantes** a uma **Arena Gamificada de Duelos Pareados** (*pairwise comparisons*) para ranquear estatisticamente brindes e temas de palestras através do **Modelo Bradley-Terry** e **Rating Elo**.

---

## 🌟 Principais Recursos

### 1. Pesquisa Oficial de Demanda e Perfil dos Estudantes
- **Identificação Completa**: Nome, E-mail, Telefone/WhatsApp com máscara dinâmica `(31) 99999-9999`.
- **Cursos da UFMG**: Mapeamento oficial das engenharias da Escola de Engenharia da UFMG e opção para outros cursos.
- **Rastreamento de Origem e 35 Iniciativas de Extensão**:
  - Detecção inteligente por parâmetro de URL (ex: `?iniciativa=MinasJr`).
  - Dropdown oficial com as 35 empresas juniores e projetos de extensão da UFMG (*Aero Jr, Baja, CPE, Cria, Emas, Fórmula, Minas Jr, UCJ, etc.*).
- **Demandas Corporativas**: Coleta em texto aberto das empresas, indústrias e setores que os alunos mais desejam ver no campus.
- **Palestras e Conteúdo**: Seleção de temas de painel (com limite de 3 opções e campo para outros temas), além de preferências de turno e horário da feira.

### 2. Gamificação de Brindes & Palestras (Bradley-Terry / Elo)
- **Cards 100% Limpos**: Exibição de foto em alta definição, título e botão de voto direto (sem IDs técnicos ou notas expostas ao aluno).
- **Palestras Filtradas por Curso**: Estudantes avaliam palestras curadas para a sua própria área de engenharia.
- **Garantia de Não-Repetição**: O algoritmo assegura que o mesmo usuário (`uid`) nunca avalie o mesmo par de opções duas vezes.
- **Atalhos de Teclado**:
  - Tecla `[1]` ou `[←]`: Escolhe a opção da esquerda
  - Tecla `[2]` ou `[→]`: Escolhe a opção da direita
  - Tecla `[Espaço]`: Pula duelo
- **Feedback Sonoro**: Sons sintéticos via Web Audio API nativo.

### 3. Painel Administrativo e Gestão de Dados
- **Área Restrita da Gestão**: Acesso protegido por senha para organizadores do evento (`admin123` por padrão, alterável no painel).
- **Exportação Completa para Planilha Excel (`.xlsx`)**:
  - `Inscritos_Formulario`: Tabela completa com respostas da pesquisa, empresas desejadas e temas.
  - `Ranking_Brindes`: Rankings de brindes ordenados por Elo, taxa de vitória e força BT ($\pi$).
  - `Ranking_Palestras`: Rankings de palestras e temas por curso.
  - `Duelos_Brindes` e `Duelos_Palestras`: Log de auditoria de cada confronto.
  - `Resumo_Executivo`: Métricas consolidadas e KPIs do evento.
- **Gerador de Links por Iniciativa**: Criação de links exclusivos para acompanhamento do engajamento de cada iniciativa parceira.

### 4. Banco de Dados SQLite Robusto e Auto-Seeding
- Persistência local transacional em `torneio.db`.
- **Auto-Seeding**: Na inicialização em ambiente limpo, o sistema popula automaticamente todos os 96 itens curados (67 brindes e 29 palestras com fotos em alta definição) a partir de `items_data.json`.

---

## 🎨 Identidade Visual (Manual de Marca)

O layout segue o Manual de Identidade Visual oficial da **Mercado em Conexão (UFMG)**:
- **Azul Primário (Deep Navy)**: `#024c76`
- **Azul Secundário (Soft Teal / Ocean)**: `#57a0bc`
- **Laranja de Destaque (Warm Vibrant Orange)**: `#f6a21c`
- **Tipografia**: `Lexend` (Google Fonts)

---

## 📁 Estrutura do Projeto

```
├── app.py                 # Aplicação FastAPI, rotas HTTP e API REST
├── database.py            # Camada SQLite, migrations e auto-seed de itens
├── tournament.py          # Matemática Bradley-Terry, cálculo Elo e matchmaking
├── exporter.py            # Exportação de planilhas Excel (.xlsx) profissionais
├── models.py              # Validações e schemas Pydantic
├── test_integration.py    # Testes unitários e de integração automatizados
├── items_data.json        # Base de dados curada com os 96 brindes e palestras
├── Pesquisa de Brindes.xlsx # Base histórica de brindes
├── torneio.db             # Banco de dados SQLite pré-configurado
├── requirements.txt       # Dependências Python
├── templates/             # Templates HTML (Jinja2)
│   ├── base.html          # Layout mestre institucional com navbar e logo oficial
│   ├── index.html         # Pesquisa de demanda + Arena de duelos pareados
│   ├── ranking.html       # Rankings detalhados Elo & Bradley-Terry (Gestão)
│   ├── admin.html         # Painel administrativo com leads e auditoria
│   └── login.html         # Autenticação da comissão organizadora
└── static/                # Recursos estáticos
    ├── css/
    │   └── style.css      # Design system oficial da Mercado em Conexão
    ├── js/
    │   └── flow.js        # Controlador do fluxo de pesquisa e duelos
    └── img/               # Logotipos e ícones oficiais
```

---

## 🚀 Como Executar

### 1. Clonar o repositório
```bash
git clone https://github.com/Pedro130505/Formulario-Torneio-Mercado-em-Conexao.git
cd Formulario-Torneio-Mercado-em-Conexao
```

### 2. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 3. Iniciar o servidor
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Acessar no Navegador
- **Pesquisa de Demanda dos Alunos:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Link com Iniciativa (ex: Minas Jr):** [http://127.0.0.1:8000/?iniciativa=MinasJr](http://127.0.0.1:8000/?iniciativa=MinasJr)
- **Área da Gestão / Painel Admin:** [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login) *(Senha padrão: `admin123`)*
- **Exportação Direta da Planilha:** [http://127.0.0.1:8000/api/exportar](http://127.0.0.1:8000/api/exportar)

### 5. Executar os Testes Automatizados
```bash
python test_integration.py
```

---

## 📐 Fundamentação Estatística

O sistema calcula em tempo real o score esperado de preferência entre duas alternativas $A$ e $B$:
$$E_A = \frac{1}{1 + 10^{(R_B - R_A)/400}}$$
$$E_B = 1 - E_A$$

A atualização dinâmica de pontuação após cada escolha é dada por:
$$R'_A = R_A + K \cdot (S_A - E_A)$$
onde $S_A = 1$ para vitória e $S_A = 0$ para derrota, com fator $K$ adaptativo para rápida convergência e estabilidade estatística. A força intrínseca no modelo Bradley-Terry é estimada como:
$$\pi_i = 10^{R_i / 400}$$
sendo proporcional à probabilidade de preferência do público universitário.
