"""
Aplicação Principal FastAPI - Sistema de Torneio Bradley-Terry / Elo.
Mercado em Conexão (UFMG) - Brindes e Temas de Palestras por Engenharia.
"""
import os
import io
import datetime
import hashlib
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Query, Form
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import (
    init_db,
    get_all_items,
    get_item_by_id,
    get_recent_duels,
    get_all_participants,
    get_stats,
    add_item,
    toggle_item_status,
    reset_ratings,
    get_connection,
    get_admin_password,
    set_admin_password,
    save_inscricao,
    get_all_inscritos,
    get_inscrito_by_uid,
    EXCEL_PATH
)
from tournament import get_next_matchup, process_vote, get_enriched_leaderboard
from exporter import generate_excel_report
from models import VotoRequest, ItemCreate, ItemUpdate, InscricaoFormRequest

# Cria diretórios de templates e static se não existirem
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "img"), exist_ok=True)

app = FastAPI(
    title="Mercado em Conexão - Gamificação & Torneio Elo",
    description="Sistema integrado de cadastro de estudantes, duelos pareados Bradley-Terry para brindes e palestras por engenharia",
    version="3.0.0"
)

# Monta arquivos estáticos e templates Jinja2
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

ADMIN_COOKIE_NAME = "torneio_admin_session"


def is_admin_authenticated(request: Request) -> bool:
    """Verifica se a sessão do administrador está ativa e válida via cookie seguro."""
    token = request.cookies.get(ADMIN_COOKIE_NAME)
    if not token:
        return False
    current_pass = get_admin_password()
    expected = hashlib.sha256(current_pass.encode()).hexdigest()
    return token == expected


@app.on_event("startup")
def startup_event():
    """Inicializa banco SQLite e aplica migrações automáticas."""
    init_db()


# ==========================================
# ROTAS PÚBLICAS DO RESPONDENTE (USUÁRIO)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def page_principal(
    request: Request,
    iniciativa: Optional[str] = None,
    canal: Optional[str] = None,
    uid: Optional[str] = None
):
    """
    Página do usuário comum:
    1. Formulário oficial do evento com lista fiel de Engenharias e 'Outros'.
    2. Duelos limpos de Brindes (apenas foto + nome + botão).
    3. Duelos limpos de Temas de Palestras filtrados pelo curso do respondente.
    4. Conclusão da participação.
    Sem acesso a rankings, IDs, notas ou funções administrativas.
    """
    iniciativa_final = iniciativa or canal or "Geral"
    admin_logged = is_admin_authenticated(request)

    # Lista oficial de engenharias UFMG mapeada a partir dos dados do formulário oficial
    engenharias_ufmg = [
        "Engenharia Aeroespacial",
        "Engenharia Ambiental",
        "Engenharia Civil",
        "Engenharia de Computação",
        "Engenharia de Controle e Automação",
        "Engenharia de Materiais",
        "Engenharia de Minas",
        "Engenharia de Produção",
        "Engenharia de Sistemas",
        "Engenharia Elétrica",
        "Engenharia Mecânica",
        "Engenharia Metalúrgica",
        "Engenharia Química",
        "Outros Cursos"
    ]

    # Lista de 35 Projetos de Extensão e Empresas Juniores da UFMG (Google Forms oficial)
    projetos_extensao_ufmg = [
        "Aero Jr",
        "Apical Jr",
        "Autobotz",
        "Avant UFMG",
        "Baja UFMG",
        "CPE Jr",
        "Cria UFMG",
        "Czar Space",
        "Dativa Jr",
        "Emas JR",
        "Farmácia Jr",
        "Fênix UFMG",
        "Finance Club",
        "Fórmula UFMG",
        "Hippocampus Jr",
        "iJunior",
        "Indérios",
        "LAFT UFMG",
        "LMN",
        "Meios Jr",
        "Milhagem UFMG",
        "Minas Jr",
        "Mude Jr",
        "Mult Jr",
        "Neuro Dynamics",
        "PJ",
        "RH Jr",
        "Sonus",
        "Solucione UFMG",
        "Tesla UFMG",
        "Trama Jr",
        "Transformare Jr",
        "Uai So Fly",
        "UCJ",
        "Vet Jr"
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "iniciativa": iniciativa_final,
            "canal": iniciativa_final,
            "uid": uid or "",
            "engenharias": engenharias_ufmg,
            "projetos_extensao": projetos_extensao_ufmg,
            "is_admin": admin_logged
        }
    )


# ==========================================
# ENDPOINTS DE FORMULÁRIO E INSCRIÇÃO
# ==========================================

@app.post("/api/inscricao")
async def api_salvar_inscricao(dados: InscricaoFormRequest):
    """Valida e armazena os dados do estudante informados no formulário oficial."""
    try:
        # Validação de e-mail básica
        if "@" not in dados.email or "." not in dados.email:
            raise HTTPException(status_code=400, detail="Por favor, informe um endereço de e-mail válido.")

        # Validação do limite de fatores de estágio
        if len(dados.fatores_estagio) > 3:
            raise HTTPException(status_code=400, detail="Selecione no máximo 3 fatores que mais chamam atenção.")

        # Validação do limite de temas de palestra / painel (máx 3)
        if len(dados.temas_painel) > 3:
            raise HTTPException(status_code=400, detail="Selecione no máximo 3 temas de palestras ou painéis.")

        save_inscricao(dados.dict())
        return {
            "status": "ok",
            "mensagem": "Inscrição validada com sucesso!",
            "uid": dados.uid,
            "nome": dados.nome,
            "curso": dados.curso,
            "iniciativa": dados.iniciativa
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar inscrição: {str(e)}")


@app.get("/api/inscricao/{uid}")
async def api_obter_inscricao(uid: str):
    """Recupera o cadastro do estudante pelo UID para manter a sessão ativa."""
    inscrito = get_inscrito_by_uid(uid)
    if inscrito:
        return {"status": "ok", "encontrado": True, "inscrito": inscrito}
    return {"status": "ok", "encontrado": False}


# ==========================================
# ENDPOINTS DE DUELOS (BRINDES E PALESTRAS)
# ==========================================

@app.get("/api/proximo-par")
async def api_proximo_par(
    uid: str = Query(...),
    canal: str = Query("geral"),
    categoria: str = Query("brinde"),
    curso: Optional[str] = Query(None)
):
    """
    Retorna o próximo confronto equilibrado no modelo Bradley-Terry.
    - categoria='brinde': retorna 2 brindes com fotos de alta qualidade.
    - categoria='palestra': retorna 2 temas filtrados de acordo com o curso do aluno.
    - Garante que a mesma combinação nunca seja repetida para o mesmo UID.
    """
    try:
        resultado = get_next_matchup(
            uid=uid,
            canal=canal,
            categoria=categoria,
            curso=curso
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voto")
async def api_registrar_voto(voto: VotoRequest):
    """Registra o voto do participante e recalcula o Elo dinamicamente."""
    try:
        resultado = process_vote(
            uid=voto.uid,
            canal=voto.canal or "geral",
            categoria=voto.categoria or "brinde",
            item_a_id=voto.item_a_id,
            item_b_id=voto.item_b_id,
            vencedor_id=voto.vencedor_id
        )
        return resultado
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# AUTENTICAÇÃO DO ADMINISTRADOR
# ==========================================

@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request, error: str = ""):
    """Tela de login com senha para a área administrativa."""
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error, "is_admin": False}
    )


@app.post("/login")
async def do_login(request: Request, senha: str = Form(...)):
    """Valida a senha de administrador e cria o cookie de sessão."""
    current_pass = get_admin_password()
    if senha.strip() == current_pass.strip():
        token = hashlib.sha256(current_pass.encode()).hexdigest()
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key=ADMIN_COOKIE_NAME, value=token, max_age=86400 * 7, httponly=True)
        return response
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Senha incorreta. Tente novamente.", "is_admin": False}
    )


@app.get("/logout")
async def do_logout():
    """Encerra a sessão do administrador."""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=ADMIN_COOKIE_NAME)
    return response


# ==========================================
# PAINEL RESTRITO DO ADMINISTRADOR (COM SENHA)
# ==========================================

@app.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request):
    """Painel de Gestão protegido por senha com KPIs, inscrições, ranking e auditoria."""
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    stats = get_stats()
    leaderboard_brindes = get_enriched_leaderboard(categoria="brinde")
    leaderboard_palestras = get_enriched_leaderboard(categoria="palestra")
    inscritos = get_all_inscritos()
    recent_duels = get_recent_duels(limit=60)
    items = get_all_items(active_only=False, order_by="categoria ASC, rating_elo DESC")
    participants = get_all_participants()

    # Cursos únicos dos inscritos para o filtro
    cursos_inscritos = sorted(list({i["curso"] for i in inscritos if i.get("curso")}))
    iniciativas_inscritos = sorted(list({i["iniciativa"] for i in inscritos if i.get("iniciativa")}))

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "stats": stats,
            "leaderboard_brindes": leaderboard_brindes,
            "leaderboard_palestras": leaderboard_palestras,
            "inscritos": inscritos,
            "cursos_inscritos": cursos_inscritos,
            "iniciativas_inscritos": iniciativas_inscritos,
            "recent_duels": recent_duels,
            "items": items,
            "participants": participants,
            "is_admin": True
        }
    )


@app.get("/ranking", response_class=HTMLResponse)
async def page_ranking(request: Request):
    """Visualização detalhada dos rankings de Brindes e Palestras com pódio (exclusivo para admin)."""
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    leaderboard_brindes = get_enriched_leaderboard(categoria="brinde")
    leaderboard_palestras = get_enriched_leaderboard(categoria="palestra")
    stats = get_stats()

    return templates.TemplateResponse(
        request=request,
        name="ranking.html",
        context={
            "leaderboard_brindes": leaderboard_brindes,
            "leaderboard_palestras": leaderboard_palestras,
            "top3_brindes": leaderboard_brindes[:3],
            "top3_palestras": leaderboard_palestras[:3],
            "stats": stats,
            "is_admin": True
        }
    )


@app.get("/api/exportar")
async def api_exportar_planilha(request: Request):
    """Gera e faz o download direto da planilha Excel (.xlsx) com múltiplas abas completas."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Acesso restrito ao administrador. Faça login em /login para exportar.")

    try:
        excel_buffer = generate_excel_report()
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Mercado_em_Conexao_Torneio_Elo_{timestamp_str}.xlsx"

        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar planilha Excel: {str(e)}")


@app.patch("/api/itens/{item_id}/status")
async def api_toggle_status(request: Request, item_id: str):
    """Ativa ou desativa um brinde ou tema de palestra no torneio."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Não autorizado")
    novo_status = toggle_item_status(item_id)
    return {"status": "ok", "ativo": novo_status, "mensagem": "Status atualizado com sucesso!"}


@app.post("/api/admin/alterar-senha")
async def api_alterar_senha(request: Request, payload: dict):
    """Altera a senha de acesso administrativo."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Não autorizado")

    nova_senha = payload.get("nova_senha", "").strip()
    if len(nova_senha) < 3:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 3 caracteres.")

    set_admin_password(nova_senha)
    token = hashlib.sha256(nova_senha.encode()).hexdigest()
    response = JSONResponse({"status": "ok", "mensagem": "Senha alterada com sucesso!"})
    response.set_cookie(key=ADMIN_COOKIE_NAME, value=token, max_age=86400 * 7, httponly=True)
    return response


@app.post("/api/admin/reset")
async def api_reset_ratings(request: Request, payload: dict):
    """Reinicia os ratings Elo e limpa duelos (com confirmação por segurança)."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Não autorizado")
    senha = payload.get("confirmacao", "")
    if senha != "CONFIRMAR_RESET":
        raise HTTPException(status_code=400, detail="Confirmação de segurança incorreta.")
    reset_ratings()
    return {"status": "ok", "mensagem": "Ratings e duelos reiniciados com sucesso!"}


if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Mercado em Conexão - Sistema Bradley-Terry / Elo")
    print("🌐 Formulário & Duelos dos Estudantes:  http://127.0.0.1:8000")
    print("🔒 Login do Administrador:             http://127.0.0.1:8000/login")
    print("📊 Painel de Análises & Leads:          http://127.0.0.1:8000/admin")
    print("🔑 Senha Padrão Inicial:               admin123")
    print("=" * 65)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
