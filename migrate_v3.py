"""
Migração do banco de dados para a Versão 3:
- Adiciona categoria ('brinde' ou 'palestra') e curso_alvo em itens
- Adiciona categoria em respostas
- Cria tabela de inscritos_form (réplica fiel do Google Forms do evento)
- Insere temas de palestras curados para Mercado em Conexão (UFMG) com imagens
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "torneio.db")

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Colunas em 'itens'
    cursor.execute("PRAGMA table_info(itens);")
    cols_itens = [c[1] for c in cursor.fetchall()]
    if "categoria" not in cols_itens:
        cursor.execute("ALTER TABLE itens ADD COLUMN categoria TEXT DEFAULT 'brinde';")
        print("[Migração] Coluna 'categoria' adicionada a itens.")
    if "curso_alvo" not in cols_itens:
        cursor.execute("ALTER TABLE itens ADD COLUMN curso_alvo TEXT DEFAULT 'todos';")
        print("[Migração] Coluna 'curso_alvo' adicionada a itens.")

    # 2. Colunas em 'respostas'
    cursor.execute("PRAGMA table_info(respostas);")
    cols_resp = [c[1] for c in cursor.fetchall()]
    if "categoria" not in cols_resp:
        cursor.execute("ALTER TABLE respostas ADD COLUMN categoria TEXT DEFAULT 'brinde';")
        print("[Migração] Coluna 'categoria' adicionada a respostas.")

    # 3. Tabela de Inscrições do Formulário
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inscritos_form (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE NOT NULL,
            iniciativa TEXT DEFAULT 'Geral',
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            universidade TEXT NOT NULL,
            curso TEXT NOT NULL,
            ano_graduacao TEXT NOT NULL,
            vagas_6meses TEXT NOT NULL,
            fatores_estagio TEXT NOT NULL,
            como_conheceu TEXT NOT NULL,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inscritos_uid ON inscritos_form(uid);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inscritos_curso ON inscritos_form(curso);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inscritos_iniciativa ON inscritos_form(iniciativa);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_categoria ON itens(categoria);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_respostas_categoria ON respostas(categoria);")

    # Garante que todos os itens existentes sejam da categoria 'brinde'
    cursor.execute("UPDATE itens SET categoria = 'brinde' WHERE categoria IS NULL OR categoria = '';")

    # 4. Inserir Temas de Palestras
    palestras = [
        # GERAL / TRANSVERSAL (Aparece para todos e para Outros)
        {
            "id": "PAL_TRANSICAO_MERCADO",
            "nome": "Transição Universidade ➔ Mercado: Como se Destacar em Processos Seletivos",
            "categoria": "palestra",
            "curso_alvo": "todos",
            "imagem_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_IA_CORPORATIVO",
            "nome": "Inteligência Artificial Generativa no Mercado Corporativo: Do Hype à Prática",
            "categoria": "palestra",
            "curso_alvo": "todos",
            "imagem_url": "https://images.unsplash.com/photo-1677442136019-21780efad99a?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_LIDERANCA_JOVEM",
            "nome": "Liderança Jovem & Soft Skills: O que as Grandes Empresas Esperam dos Recém-Formados",
            "categoria": "palestra",
            "curso_alvo": "todos",
            "imagem_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_CONSULTORIA_FINANCAS",
            "nome": "Consultoria Estratégica & Mercado Financeiro: Como Ingressar e Acelerar Carreira",
            "categoria": "palestra",
            "curso_alvo": "todos",
            "imagem_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_EMPREENDEDORISMO_TECH",
            "nome": "Empreendedorismo Tech: Como Fundar Startups e Validar Ideias no Ecossistema Universitário",
            "categoria": "palestra",
            "curso_alvo": "todos",
            "imagem_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA CIVIL
        {
            "id": "PAL_CIVIL_BIM",
            "nome": "BIM 5D e Gêmeos Digitais na Gestão de Obras Complexas e Infraestrutura",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Civil",
            "imagem_url": "https://images.unsplash.com/photo-1541888946425-d0fbb18086f6?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_CIVIL_SUSTENTABILIDADE",
            "nome": "Sustentabilidade e Concreto de Baixo Carbono na Construção Civil Moderna",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Civil",
            "imagem_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_CIVIL_INFRAESTRUTURA",
            "nome": "Megaprojetos de Infraestrutura e Concessões: Desafios Técnicos e Financeiros",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Civil",
            "imagem_url": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_CIVIL_MODULAR",
            "nome": "Construção Modular Off-Site e Tecnologias de Industrialização da Construção",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Civil",
            "imagem_url": "https://images.unsplash.com/photo-1590381105924-c72589b9ef3f?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA MECÂNICA & AEROESPACIAL
        {
            "id": "PAL_MEC_AERODINAMICA",
            "nome": "CFD e Simulação Multifísica Avançada na Indústria Aeroespacial e Automotiva",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Mecânica,Engenharia Aeroespacial",
            "imagem_url": "https://images.unsplash.com/photo-1517976487507-5d3b3a997845?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_MEC_MOBILIDADE_ELETRICA",
            "nome": "Mobilidade Elétrica, Powertrains Híbridos e Tecnologias de Descarbonização Veicular",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Mecânica,Engenharia Aeroespacial",
            "imagem_url": "https://images.unsplash.com/photo-1558441719-aa34bbe5f347?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_MEC_MANUTENCAO_PREDITIVA",
            "nome": "Manutenção Preditiva e Indústria 4.0: Monitoramento de Vibração com IA e IoT",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Mecânica,Engenharia Aeroespacial",
            "imagem_url": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_MEC_COMPOSITOS",
            "nome": "Materiais Compósitos e Ligas Avançadas para Estruturas Aeronáuticas de Alta Performance",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Mecânica,Engenharia Aeroespacial",
            "imagem_url": "https://images.unsplash.com/photo-1569683795645-b62e50fbf103?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA DE CONTROLE E AUTOMAÇÃO & ENGENHARIA ELÉTRICA
        {
            "id": "PAL_ELE_SMART_GRIDS",
            "nome": "Transição Energética & Redes Inteligentes (Smart Grids) no Mercado Livre de Energia",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Elétrica,Engenharia de Controle e Automação",
            "imagem_url": "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_ELE_ROBOTICA_INDUSTRIAL",
            "nome": "Robótica Móvel Autônoma (AMR) e Visão Computacional em Chão de Fábrica",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Elétrica,Engenharia de Controle e Automação",
            "imagem_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_ELE_EMBARCADOS_IOT",
            "nome": "Sistemas Embarcados de Tempo Real e Conectividade 5G Industrial",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Elétrica,Engenharia de Controle e Automação",
            "imagem_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_ELE_HIDROGENIO_VERDE",
            "nome": "Hidrogênio Verde e Armazenamento de Energia para a Descarbonização da Matriz",
            "categoria": "palestra",
            "curso_alvo": "Engenharia Elétrica,Engenharia de Controle e Automação",
            "imagem_url": "https://images.unsplash.com/photo-1509391365360-2e959784a276?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA DE PRODUÇÃO
        {
            "id": "PAL_PROD_SUPPLY_CHAIN",
            "nome": "Supply Chain 4.0: Resiliência Logística, Algoritmos de Otimização e Previsão de Demanda",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Produção",
            "imagem_url": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_PROD_LEAN_SIX_SIGMA",
            "nome": "Lean Six Sigma e Excelência Operacional aliada à Transformação Digital",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Produção",
            "imagem_url": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_PROD_PRODUCT_MANAGEMENT",
            "nome": "Product Management em Tech: Como Engenheiros de Produção Lideram Produtos Digitais",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Produção",
            "imagem_url": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_PROD_DATA_DRIVEN",
            "nome": "Data-Driven Decision Making: Da Engenharia de Dados à Tomada de Decisão Executiva",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Produção",
            "imagem_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA DE COMPUTAÇÃO & SISTEMAS
        {
            "id": "PAL_COMP_CLOUD_ESCALAVEL",
            "nome": "Arquiteturas Escaláveis em Nuvem, Microsserviços e Engenharia de Resiliência",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Computação,Engenharia de Sistemas",
            "imagem_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_COMP_LLMS_DEV",
            "nome": "Engenharia de Software com IA Generativa, Agentes Autônomos e LLMs",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Computação,Engenharia de Sistemas",
            "imagem_url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_COMP_CYBERSECURITY",
            "nome": "Cybersecurity & Defesa Cibernética em Infraestruturas Críticas e Fintechs",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Computação,Engenharia de Sistemas",
            "imagem_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_COMP_BIGDATA_STREAMING",
            "nome": "Engenharia de Dados em Streaming: Processamento de Dados em Tempo Real em Larga Escala",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Computação,Engenharia de Sistemas",
            "imagem_url": "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&auto=format&fit=crop&q=80"
        },

        # ENGENHARIA QUÍMICA, MINAS, METALÚRGICA, MATERIAIS & AMBIENTAL
        {
            "id": "PAL_MIN_OPERACAO_AUTONOMA",
            "nome": "Mineração 4.0: Caminhões Autônomos, Centros de Operações Integradas e IA em Mina",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Minas,Engenharia Metalúrgica,Engenharia Química,Engenharia de Materiais,Engenharia Ambiental",
            "imagem_url": "https://images.unsplash.com/photo-1578328819058-b69f3a3b0f6b?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_QUI_DESCARBONIZACAO_SIDERURGIA",
            "nome": "Aço Verde & Descarbonização na Indústria Siderúrgica com Redução Direta por Hidrogênio",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Minas,Engenharia Metalúrgica,Engenharia Química,Engenharia de Materiais,Engenharia Ambiental",
            "imagem_url": "https://images.unsplash.com/photo-1504917599217-d4dc5ebe6122?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_MAT_BATERIAS_LITIO",
            "nome": "Baterias de Lítio e Minerais Estratégicos: O Papel do Brasil na Cadeia Global de Eletrificação",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Minas,Engenharia Metalúrgica,Engenharia Química,Engenharia de Materiais,Engenharia Ambiental",
            "imagem_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=800&auto=format&fit=crop&q=80"
        },
        {
            "id": "PAL_AMB_ESG_REJEITOS",
            "nome": "Gestão ESG & Reaproveitamento Tecnológico de Rejeitos em Obras e Pavimentação",
            "categoria": "palestra",
            "curso_alvo": "Engenharia de Minas,Engenharia Metalúrgica,Engenharia Química,Engenharia de Materiais,Engenharia Ambiental",
            "imagem_url": "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=800&auto=format&fit=crop&q=80"
        }
    ]

    for p in palestras:
        cursor.execute("""
            INSERT INTO itens (id, nome, descricao, rating_elo, jogos, vitorias, derrotas, ativo, categoria, curso_alvo, imagem_url)
            VALUES (?, ?, '', 1000.0, 0, 0, 0, 1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome = excluded.nome,
                categoria = excluded.categoria,
                curso_alvo = excluded.curso_alvo,
                imagem_url = excluded.imagem_url
        """, (p["id"], p["nome"], p["categoria"], p["curso_alvo"], p["imagem_url"]))

    conn.commit()
    print(f"[Migração] {len(palestras)} temas de palestras sincronizados com sucesso!")
    conn.close()

if __name__ == "__main__":
    run_migration()
