"""
Camada de Acesso a Dados (SQLite) com suporte a:
- Duelos de Brindes e Palestras por Bradley-Terry / Elo
- Filtragem dinâmica por Curso / Engenharia para Palestras
- Armazenamento e validação de inscrições (réplica do formulário oficial de eventos MeC/UFMG)
- Auditoria de votos por Iniciativa e UID com garantia de não repetição de duelos
"""
import os
import sqlite3
import datetime
import json
from typing import List, Dict, Any, Optional, Set, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "torneio.db")
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Pesquisa de Brindes.xlsx")


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Cria e retorna uma conexão SQLite com suporte a dicionários."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DB_PATH, excel_path: str = EXCEL_PATH):
    """Cria as tabelas necessárias e executa migrações automáticas de schema."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Tabela de Itens (Brindes e Temas de Palestras)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                rating_elo REAL DEFAULT 1000.0,
                jogos INTEGER DEFAULT 0,
                vitorias INTEGER DEFAULT 0,
                derrotas INTEGER DEFAULT 0,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                imagem_url TEXT DEFAULT '',
                categoria TEXT DEFAULT 'brinde',
                curso_alvo TEXT DEFAULT 'todos'
            );
        """)

        # 2. Tabela de Inscrições / Formulário Oficial do Estudante
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inscritos_form (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE NOT NULL,
                iniciativa TEXT DEFAULT 'Geral',
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                telefone TEXT NOT NULL,
                universidade TEXT DEFAULT 'UFMG - Universidade Federal de Minas Gerais',
                curso TEXT NOT NULL,
                ano_graduacao TEXT DEFAULT '',
                vagas_6meses TEXT DEFAULT '',
                fatores_estagio TEXT DEFAULT '',
                como_conheceu TEXT DEFAULT '',
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                como_soube_opcao TEXT DEFAULT '',
                projeto_extensao TEXT DEFAULT '',
                empresas_desejadas TEXT DEFAULT '',
                temas_painel TEXT DEFAULT '',
                tema_outro TEXT DEFAULT '',
                periodo_palestras TEXT DEFAULT '',
                horario_feira TEXT DEFAULT ''
            );
        """)

        # 3. Tabela de Histórico de Duelos / Respostas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS respostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                uid TEXT NOT NULL,
                canal TEXT DEFAULT 'geral',
                categoria TEXT DEFAULT 'brinde',
                item_a_id TEXT NOT NULL,
                item_b_id TEXT NOT NULL,
                vencedor_id TEXT NOT NULL,
                perdedor_id TEXT NOT NULL,
                elo_a_antes REAL,
                elo_b_antes REAL,
                elo_a_depois REAL,
                elo_b_depois REAL,
                delta_elo REAL,
                FOREIGN KEY (item_a_id) REFERENCES itens(id) ON DELETE CASCADE,
                FOREIGN KEY (item_b_id) REFERENCES itens(id) ON DELETE CASCADE
            );
        """)

        # 4. Tabela de Participantes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participantes (
                uid TEXT PRIMARY KEY,
                canal TEXT DEFAULT 'geral',
                total_votos INTEGER DEFAULT 0,
                criado_em TEXT,
                ultimo_voto TEXT
            );
        """)

        # 5. Tabela de Configurações do Sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            );
        """)
        cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('admin_password', 'admin123');")

        # Índices essenciais para consultas rápidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_respostas_uid ON respostas(uid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_respostas_vencedor ON respostas(vencedor_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_respostas_categoria ON respostas(categoria);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_categoria ON itens(categoria);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_rating ON itens(rating_elo DESC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_jogos ON itens(jogos ASC);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inscritos_uid ON inscritos_form(uid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inscritos_curso ON inscritos_form(curso);")

        # Se a tabela de itens estiver vazia, popula automaticamente a partir de items_data.json
        cursor.execute("SELECT COUNT(*) FROM itens")
        if cursor.fetchone()[0] == 0:
            json_file = os.path.join(os.path.dirname(__file__), "items_data.json")
            if os.path.exists(json_file):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        itens_iniciais = json.load(f)
                    for item in itens_iniciais:
                        cursor.execute("""
                            INSERT OR IGNORE INTO itens (id, nome, descricao, rating_elo, jogos, vitorias, derrotas, ativo, imagem_url, categoria, curso_alvo)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"],
                            item["nome"],
                            item.get("descricao", ""),
                            item.get("rating_elo", 1000.0),
                            item.get("jogos", 0),
                            item.get("vitorias", 0),
                            item.get("derrotas", 0),
                            item.get("ativo", 1),
                            item.get("imagem_url", ""),
                            item.get("categoria", "brinde"),
                            item.get("curso_alvo", "todos")
                        ))
                except Exception as e:
                    print(f"Aviso ao inicializar itens padrão: {e}")

        conn.commit()


# ==========================================
# GESTÃO DO FORMULÁRIO DE INSCRIÇÃO
# ==========================================

def save_inscricao(dados: Dict[str, Any]) -> int:
    """Salva ou atualiza as respostas do formulário de pesquisa do estudante."""
    fatores = dados.get("fatores_estagio", [])
    if isinstance(fatores, list):
        fatores_str = "; ".join(fatores)
    else:
        fatores_str = str(fatores or "")

    temas = dados.get("temas_painel", [])
    if isinstance(temas, list):
        temas_str = "; ".join(temas)
    else:
        temas_str = str(temas or "")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inscritos_form (
                uid, iniciativa, nome, email, telefone, universidade, curso,
                ano_graduacao, vagas_6meses, fatores_estagio, como_conheceu, criado_em,
                como_soube_opcao, projeto_extensao, empresas_desejadas, temas_painel,
                tema_outro, periodo_palestras, horario_feira
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                iniciativa = excluded.iniciativa,
                nome = excluded.nome,
                email = excluded.email,
                telefone = excluded.telefone,
                universidade = excluded.universidade,
                curso = excluded.curso,
                ano_graduacao = excluded.ano_graduacao,
                vagas_6meses = excluded.vagas_6meses,
                fatores_estagio = excluded.fatores_estagio,
                como_conheceu = excluded.como_conheceu,
                como_soube_opcao = excluded.como_soube_opcao,
                projeto_extensao = excluded.projeto_extensao,
                empresas_desejadas = excluded.empresas_desejadas,
                temas_painel = excluded.temas_painel,
                tema_outro = excluded.tema_outro,
                periodo_palestras = excluded.periodo_palestras,
                horario_feira = excluded.horario_feira
        """, (
            dados["uid"],
            dados.get("iniciativa", "Geral"),
            dados["nome"],
            dados["email"],
            dados["telefone"],
            dados.get("universidade", "UFMG - Universidade Federal de Minas Gerais"),
            dados["curso"],
            dados.get("ano_graduacao", ""),
            dados.get("vagas_6meses", ""),
            fatores_str,
            dados.get("como_conheceu", ""),
            now_str,
            dados.get("como_soube_opcao", ""),
            dados.get("projeto_extensao", ""),
            dados.get("empresas_desejadas", ""),
            temas_str,
            dados.get("tema_outro", ""),
            dados.get("periodo_palestras", ""),
            dados.get("horario_feira", "")
        ))
        conn.commit()
        return cursor.lastrowid


def get_inscrito_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """Busca o cadastro do estudante pelo seu identificador único."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM inscritos_form WHERE uid = ?", (uid,)).fetchone()
        return dict(row) if row else None


def get_all_inscritos() -> List[Dict[str, Any]]:
    """Retorna todas as inscrições ordenadas pela mais recente."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM inscritos_form ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


# ==========================================
# ACESSO A ITENS E DUELOS
# ==========================================

def get_all_items(
    active_only: bool = True,
    order_by: str = "rating_elo DESC",
    categoria: Optional[str] = None,
    curso: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna os itens cadastrados no sistema.
    Permite filtrar por categoria ('brinde' ou 'palestra') e por curso específico do aluno.
    """
    with get_connection() as conn:
        query = "SELECT * FROM itens WHERE 1=1"
        params: List[Any] = []

        if active_only:
            query += " AND ativo = 1"

        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)

        if categoria == "palestra" and curso:
            # Seleciona tópicos gerais ("todos") ou que contemplem o curso do aluno
            query += " AND (curso_alvo = 'todos' OR instr(curso_alvo, ?) > 0)"
            params.append(curso)

        query += f" ORDER BY {order_by}"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_item_by_id(item_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM itens WHERE id = ?", (item_id,)).fetchone()
        return dict(row) if row else None


def get_user_votes_count(uid: str, categoria: Optional[str] = None) -> int:
    with get_connection() as conn:
        if categoria:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM respostas WHERE uid = ? AND categoria = ?",
                (uid, categoria)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM respostas WHERE uid = ?",
                (uid,)
            ).fetchone()
        return row["total"] if row else 0


def get_user_voted_pairs(uid: str, categoria: Optional[str] = None) -> Set[frozenset]:
    """Retorna o conjunto de pares (frozenset) que o usuário já respondeu, filtrado por categoria se informado."""
    with get_connection() as conn:
        if categoria:
            rows = conn.execute(
                "SELECT item_a_id, item_b_id FROM respostas WHERE uid = ? AND categoria = ?",
                (uid, categoria)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT item_a_id, item_b_id FROM respostas WHERE uid = ?",
                (uid,)
            ).fetchall()
        return {frozenset([r["item_a_id"], r["item_b_id"]]) for r in rows}


def record_match_vote(
    uid: str,
    canal: str,
    item_a_id: str,
    item_b_id: str,
    vencedor_id: str,
    perdedor_id: str,
    elo_a_antes: float,
    elo_b_antes: float,
    elo_a_depois: float,
    elo_b_depois: float,
    delta_elo: float,
    categoria: str = "brinde"
) -> int:
    """Registra o duelo, atualiza os itens e o participante atomicamente."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Insere resposta
        cursor.execute("""
            INSERT INTO respostas (
                timestamp, uid, canal, categoria, item_a_id, item_b_id,
                vencedor_id, perdedor_id,
                elo_a_antes, elo_b_antes, elo_a_depois, elo_b_depois, delta_elo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_str, uid, canal, categoria, item_a_id, item_b_id,
            vencedor_id, perdedor_id,
            elo_a_antes, elo_b_antes, elo_a_depois, elo_b_depois, delta_elo
        ))
        match_id = cursor.lastrowid

        # 2. Atualiza item A
        is_a_winner = (vencedor_id == item_a_id)
        cursor.execute("""
            UPDATE itens SET
                rating_elo = ?,
                jogos = jogos + 1,
                vitorias = vitorias + ?,
                derrotas = derrotas + ?
            WHERE id = ?
        """, (elo_a_depois, 1 if is_a_winner else 0, 0 if is_a_winner else 1, item_a_id))

        # 3. Atualiza item B
        is_b_winner = (vencedor_id == item_b_id)
        cursor.execute("""
            UPDATE itens SET
                rating_elo = ?,
                jogos = jogos + 1,
                vitorias = vitorias + ?,
                derrotas = derrotas + ?
            WHERE id = ?
        """, (elo_b_depois, 1 if is_b_winner else 0, 0 if is_b_winner else 1, item_b_id))

        # 4. Atualiza participante
        cursor.execute("""
            INSERT INTO participantes (uid, canal, total_votos, criado_em, ultimo_voto)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                canal = excluded.canal,
                total_votos = total_votos + 1,
                ultimo_voto = excluded.ultimo_voto
        """, (uid, canal, now_str, now_str))

        conn.commit()
        return match_id


def get_recent_duels(limit: int = 50, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        query = """
            SELECT 
                r.id, r.timestamp, r.uid, r.canal, r.categoria,
                r.item_a_id, ia.nome AS item_a_nome, ia.imagem_url AS item_a_imagem,
                r.item_b_id, ib.nome AS item_b_nome, ib.imagem_url AS item_b_imagem,
                r.vencedor_id, iv.nome AS vencedor_nome,
                r.perdedor_id, ip.nome AS perdedor_nome,
                r.elo_a_antes, r.elo_b_antes,
                r.elo_a_depois, r.elo_b_depois,
                r.delta_elo
            FROM respostas r
            LEFT JOIN itens ia ON r.item_a_id = ia.id
            LEFT JOIN itens ib ON r.item_b_id = ib.id
            LEFT JOIN itens iv ON r.vencedor_id = iv.id
            LEFT JOIN itens ip ON r.perdedor_id = ip.id
        """
        params: List[Any] = []
        if categoria:
            query += " WHERE r.categoria = ?"
            params.append(categoria)
        query += " ORDER BY r.id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_all_duels(categoria: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        query = """
            SELECT 
                r.id, r.timestamp, r.uid, r.canal, r.categoria,
                r.item_a_id, ia.nome AS item_a_nome,
                r.item_b_id, ib.nome AS item_b_nome,
                r.vencedor_id, iv.nome AS vencedor_nome,
                r.perdedor_id, ip.nome AS perdedor_nome,
                r.elo_a_antes, r.elo_b_antes,
                r.elo_a_depois, r.elo_b_depois,
                r.delta_elo
            FROM respostas r
            LEFT JOIN itens ia ON r.item_a_id = ia.id
            LEFT JOIN itens ib ON r.item_b_id = ib.id
            LEFT JOIN itens iv ON r.vencedor_id = iv.id
            LEFT JOIN itens ip ON r.perdedor_id = ip.id
        """
        params: List[Any] = []
        if categoria:
            query += " WHERE r.categoria = ?"
            params.append(categoria)
        query += " ORDER BY r.id ASC"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_all_participants() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT p.uid, p.canal, p.total_votos, p.criado_em, p.ultimo_voto,
                   f.nome, f.email, f.curso, f.universidade
            FROM participantes p
            LEFT JOIN inscritos_form f ON p.uid = f.uid
            ORDER BY p.total_votos DESC, p.ultimo_voto DESC
        """).fetchall()
        return [dict(r) for r in rows]


def get_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        total_itens = cursor.execute("SELECT COUNT(*) AS c FROM itens").fetchone()["c"]
        itens_brindes = cursor.execute("SELECT COUNT(*) AS c FROM itens WHERE categoria = 'brinde' AND ativo = 1").fetchone()["c"]
        itens_palestras = cursor.execute("SELECT COUNT(*) AS c FROM itens WHERE categoria = 'palestra' AND ativo = 1").fetchone()["c"]
        
        total_duelos = cursor.execute("SELECT COUNT(*) AS c FROM respostas").fetchone()["c"]
        duelos_brindes = cursor.execute("SELECT COUNT(*) AS c FROM respostas WHERE categoria = 'brinde'").fetchone()["c"]
        duelos_palestras = cursor.execute("SELECT COUNT(*) AS c FROM respostas WHERE categoria = 'palestra'").fetchone()["c"]
        
        total_part = cursor.execute("SELECT COUNT(*) AS c FROM participantes").fetchone()["c"]
        total_inscritos = cursor.execute("SELECT COUNT(*) AS c FROM inscritos_form").fetchone()["c"]

        # Ranking resumo Brindes
        lider_brinde = cursor.execute("""
            SELECT nome, rating_elo FROM itens WHERE categoria = 'brinde' AND ativo = 1 ORDER BY rating_elo DESC LIMIT 1
        """).fetchone()

        # Ranking resumo Palestras
        lider_palestra = cursor.execute("""
            SELECT nome, rating_elo FROM itens WHERE categoria = 'palestra' AND ativo = 1 ORDER BY rating_elo DESC LIMIT 1
        """).fetchone()

        return {
            "total_itens": total_itens,
            "itens_brindes": itens_brindes,
            "itens_palestras": itens_palestras,
            "total_duelos": total_duelos,
            "duelos_brindes": duelos_brindes,
            "duelos_palestras": duelos_palestras,
            "total_participantes": total_part,
            "total_inscritos": total_inscritos,
            "brinde_lider": lider_brinde["nome"] if lider_brinde else "Nenhum",
            "brinde_lider_elo": lider_brinde["rating_elo"] if lider_brinde else 1000.0,
            "palestra_lider": lider_palestra["nome"] if lider_palestra else "Nenhuma",
            "palestra_lider_elo": lider_palestra["rating_elo"] if lider_palestra else 1000.0,
        }


def add_item(id_item: str, nome: str, descricao: str = "", imagem_url: str = "", categoria: str = "brinde", curso_alvo: str = "todos"):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO itens (id, nome, descricao, rating_elo, jogos, vitorias, derrotas, ativo, imagem_url, categoria, curso_alvo)
            VALUES (?, ?, ?, 1000.0, 0, 0, 0, 1, ?, ?, ?)
        """, (id_item, nome, descricao, imagem_url, categoria, curso_alvo))
        conn.commit()


def toggle_item_status(item_id: str) -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT ativo FROM itens WHERE id = ?", (item_id,)).fetchone()
        if not row:
            return 0
        novo_status = 0 if row["ativo"] == 1 else 1
        conn.execute("UPDATE itens SET ativo = ? WHERE id = ?", (novo_status, item_id))
        conn.commit()
        return novo_status


def reset_ratings():
    with get_connection() as conn:
        conn.execute("UPDATE itens SET rating_elo = 1000.0, jogos = 0, vitorias = 0, derrotas = 0;")
        conn.execute("DELETE FROM respostas;")
        conn.execute("DELETE FROM participantes;")
        conn.commit()


def get_admin_password() -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT valor FROM configuracoes WHERE chave = 'admin_password'").fetchone()
        return row["valor"] if row else "admin123"


def set_admin_password(nova_senha: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO configuracoes (chave, valor) VALUES ('admin_password', ?) ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
            (nova_senha,)
        )
        conn.commit()
