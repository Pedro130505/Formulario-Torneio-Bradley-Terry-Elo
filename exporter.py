"""
Módulo de Exportação Profissional para Planilhas Excel (.xlsx) com múltiplas abas estilizadas.
Identidade Visual Mercado em Conexão (UFMG).
"""
import io
import datetime
from typing import Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from database import (
    get_all_duels,
    get_all_participants,
    get_all_inscritos,
    get_stats
)
from tournament import get_enriched_leaderboard


def generate_excel_report() -> io.BytesIO:
    """
    Gera um relatório executivo completo em formato Excel (.xlsx) contendo:
    1. Inscritos no Formulário (Dados dos estudantes, cursos de engenharia, pretensões)
    2. Ranking Geral de Brindes (Bradley-Terry e Elo)
    3. Ranking Geral de Temas de Palestras (Por Curso/Engenharia)
    4. Auditoria de Duelos de Brindes
    5. Auditoria de Duelos de Palestras
    6. Painel Executivo de Estatísticas e Métricas de Iniciativas
    """
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Cores Oficiais Mercado em Conexão
    COLOR_PRIMARY = "024C76"     # Deep Navy
    COLOR_SECONDARY = "57A0BC"   # Soft Blue / Teal
    COLOR_ACCENT = "F6A21C"      # Vibrant Orange
    COLOR_LIGHT = "F0F4F8"       # Light Slate
    COLOR_WHITE = "FFFFFF"

    # Estilos Visuais Padronizados
    header_fill = PatternFill(start_color=COLOR_PRIMARY, end_color=COLOR_PRIMARY, fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color=COLOR_WHITE)

    sub_header_fill = PatternFill(start_color=COLOR_SECONDARY, end_color=COLOR_SECONDARY, fill_type="solid")
    sub_header_font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WHITE)

    accent_fill = PatternFill(start_color=COLOR_ACCENT, end_color=COLOR_ACCENT, fill_type="solid")
    accent_font = Font(name="Segoe UI", size=11, bold=True, color=COLOR_WHITE)

    zebra_fill = PatternFill(start_color=COLOR_LIGHT, end_color=COLOR_LIGHT, fill_type="solid")
    white_fill = PatternFill(start_color=COLOR_WHITE, end_color=COLOR_WHITE, fill_type="solid")

    regular_font = Font(name="Segoe UI", size=10)
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    title_font = Font(name="Segoe UI", size=14, bold=True, color=COLOR_PRIMARY)

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    grid_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

    # ==========================================
    # ABA 1: Inscritos no Formulário
    # ==========================================
    ws_inscritos = wb.create_sheet(title="Inscritos_Formulario")
    ws_inscritos.views.sheetView[0].showGridLines = True

    ws_inscritos.cell(row=1, column=1, value="📋 Mercado em Conexão - Respostas do Formulário Oficial").font = title_font
    ws_inscritos.cell(row=2, column=1, value=f"Exportado em: {now_str}").font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    headers_inscritos = [
        "ID", "UID", "Data de Envio", "Iniciativa / Canal", "Nome Completo",
        "Email de Contato", "Telefone / WhatsApp", "Universidade", "Curso / Engenharia",
        "Como Ficou Sabendo", "Projeto de Extensão / EJ",
        "Empresas Desejadas", "Temas de Palestra Escolhidos", "Outro Tema Sugerido",
        "Melhor Período Palestras", "Melhor Horário Feira"
    ]

    for col_idx, header in enumerate(headers_inscritos, start=1):
        cell = ws_inscritos.cell(row=4, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = grid_border

    inscritos = get_all_inscritos()
    for row_idx, insc in enumerate(inscritos, start=5):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        cells = [
            (insc["id"], align_center),
            (insc["uid"], align_center),
            (insc["criado_em"], align_center),
            (insc["iniciativa"], align_center),
            (insc["nome"], align_left),
            (insc["email"], align_left),
            (insc["telefone"], align_center),
            (insc.get("universidade", "UFMG"), align_left),
            (insc["curso"], align_left),
            (insc.get("como_soube_opcao", ""), align_left),
            (insc.get("projeto_extensao", ""), align_left),
            (insc.get("empresas_desejadas", ""), align_left),
            (insc.get("temas_painel", ""), align_left),
            (insc.get("tema_outro", ""), align_left),
            (insc.get("periodo_palestras", ""), align_center),
            (insc.get("horario_feira", ""), align_center)
        ]
        for col_idx, (val, alignment) in enumerate(cells, start=1):
            c = ws_inscritos.cell(row=row_idx, column=col_idx, value=val)
            c.fill = fill
            c.font = regular_font
            c.alignment = alignment
            c.border = grid_border

    # ==========================================
    # ABA 2: Ranking de Brindes
    # ==========================================
    ws_brindes = wb.create_sheet(title="Ranking_Brindes")
    ws_brindes.views.sheetView[0].showGridLines = True

    ws_brindes.cell(row=1, column=1, value="🎁 Ranking Oficial de Brindes - Modelo Bradley-Terry / Elo").font = title_font
    ws_brindes.cell(row=2, column=1, value=f"Exportado em: {now_str}").font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    headers_ranking = [
        "Posição", "ID", "Nome do Item", "Rating Elo", "Tier",
        "Total Duelos", "Vitórias", "Derrotas", "Taxa de Vitória",
        "Força BT (π)", "Chance vs Média", "Status"
    ]

    for col_idx, header in enumerate(headers_ranking, start=1):
        cell = ws_brindes.cell(row=4, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = grid_border

    leaderboard_brindes = get_enriched_leaderboard(categoria="brinde")
    for row_idx, item in enumerate(leaderboard_brindes, start=5):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        cells = [
            (item["posicao"], align_center, "0"),
            (item["id"], align_center, None),
            (item["nome"], align_left, None),
            (round(item["rating_elo"], 1), align_right, "0.0"),
            (item["tier"], align_center, None),
            (item["jogos"], align_center, "0"),
            (item["vitorias"], align_center, "0"),
            (item["derrotas"], align_center, "0"),
            (item["taxa_vitoria"] / 100.0, align_right, "0.0%"),
            (round(item["forca_bt"], 3), align_right, "0.000"),
            (item["prob_vitoria_media"] / 100.0, align_right, "0.0%"),
            ("Ativo" if item["ativo"] == 1 else "Inativo", align_center, None)
        ]
        for col_idx, (val, alignment, num_fmt) in enumerate(cells, start=1):
            c = ws_brindes.cell(row=row_idx, column=col_idx, value=val)
            c.fill = fill
            c.font = bold_font if col_idx in (1, 4) else regular_font
            c.alignment = alignment
            c.border = grid_border
            if num_fmt:
                c.number_format = num_fmt

    # ==========================================
    # ABA 3: Ranking de Temas de Palestras
    # ==========================================
    ws_palestras = wb.create_sheet(title="Ranking_Palestras")
    ws_palestras.views.sheetView[0].showGridLines = True

    ws_palestras.cell(row=1, column=1, value="🎤 Ranking de Temas de Palestras - Preferência Universitária").font = title_font
    ws_palestras.cell(row=2, column=1, value=f"Exportado em: {now_str}").font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    headers_palestras = [
        "Posição", "ID", "Tema da Palestra", "Curso(s) Alvo", "Rating Elo", "Tier",
        "Total Duelos", "Vitórias", "Derrotas", "Taxa de Vitória",
        "Força BT (π)", "Chance vs Média"
    ]

    for col_idx, header in enumerate(headers_palestras, start=1):
        cell = ws_palestras.cell(row=4, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = grid_border

    leaderboard_palestras = get_enriched_leaderboard(categoria="palestra")
    for row_idx, item in enumerate(leaderboard_palestras, start=5):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        cells = [
            (item["posicao"], align_center, "0"),
            (item["id"], align_center, None),
            (item["nome"], align_left, None),
            (item.get("curso_alvo", "todos"), align_left, None),
            (round(item["rating_elo"], 1), align_right, "0.0"),
            (item["tier"], align_center, None),
            (item["jogos"], align_center, "0"),
            (item["vitorias"], align_center, "0"),
            (item["derrotas"], align_center, "0"),
            (item["taxa_vitoria"] / 100.0, align_right, "0.0%"),
            (round(item["forca_bt"], 3), align_right, "0.000"),
            (item["prob_vitoria_media"] / 100.0, align_right, "0.0%")
        ]
        for col_idx, (val, alignment, num_fmt) in enumerate(cells, start=1):
            c = ws_palestras.cell(row=row_idx, column=col_idx, value=val)
            c.fill = fill
            c.font = bold_font if col_idx in (1, 5) else regular_font
            c.alignment = alignment
            c.border = grid_border
            if num_fmt:
                c.number_format = num_fmt

    # ==========================================
    # ABA 4: Auditoria de Duelos (Brindes)
    # ==========================================
    ws_duelos_brindes = wb.create_sheet(title="Duelos_Brindes")
    ws_duelos_brindes.views.sheetView[0].showGridLines = True

    ws_duelos_brindes.cell(row=1, column=1, value="⚔️ Histórico de Confrontos - Brindes").font = title_font

    headers_duelos = [
        "Duelo #", "Data / Hora", "Participante (UID)", "Iniciativa / Canal",
        "Opção A", "Opção B", "Vencedor", "Perdedor",
        "Elo A (Antes)", "Elo B (Antes)", "Elo A (Depois)", "Elo B (Depois)", "Variação (Δ)"
    ]

    for col_idx, header in enumerate(headers_duelos, start=1):
        cell = ws_duelos_brindes.cell(row=3, column=col_idx, value=header)
        cell.fill = sub_header_fill
        cell.font = sub_header_font
        cell.alignment = align_center
        cell.border = grid_border

    duelos_b = get_all_duels(categoria="brinde")
    for row_idx, d in enumerate(duelos_b, start=4):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        cells = [
            (d["id"], align_center),
            (d["timestamp"], align_center),
            (d["uid"], align_center),
            (d["canal"], align_center),
            (d["item_a_nome"], align_left),
            (d["item_b_nome"], align_left),
            (d["vencedor_nome"], align_left),
            (d["perdedor_nome"], align_left),
            (d["elo_a_antes"], align_right),
            (d["elo_b_antes"], align_right),
            (d["elo_a_depois"], align_right),
            (d["elo_b_depois"], align_right),
            (d["delta_elo"], align_right)
        ]
        for col_idx, (val, alignment) in enumerate(cells, start=1):
            c = ws_duelos_brindes.cell(row=row_idx, column=col_idx, value=val)
            c.fill = fill
            c.font = regular_font
            c.alignment = alignment
            c.border = grid_border

    # ==========================================
    # ABA 5: Auditoria de Duelos (Palestras)
    # ==========================================
    ws_duelos_palestras = wb.create_sheet(title="Duelos_Palestras")
    ws_duelos_palestras.views.sheetView[0].showGridLines = True

    ws_duelos_palestras.cell(row=1, column=1, value="⚔️ Histórico de Confrontos - Temas de Palestras").font = title_font

    for col_idx, header in enumerate(headers_duelos, start=1):
        cell = ws_duelos_palestras.cell(row=3, column=col_idx, value=header)
        cell.fill = sub_header_fill
        cell.font = sub_header_font
        cell.alignment = align_center
        cell.border = grid_border

    duelos_p = get_all_duels(categoria="palestra")
    for row_idx, d in enumerate(duelos_p, start=4):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        cells = [
            (d["id"], align_center),
            (d["timestamp"], align_center),
            (d["uid"], align_center),
            (d["canal"], align_center),
            (d["item_a_nome"], align_left),
            (d["item_b_nome"], align_left),
            (d["vencedor_nome"], align_left),
            (d["perdedor_nome"], align_left),
            (d["elo_a_antes"], align_right),
            (d["elo_b_antes"], align_right),
            (d["elo_a_depois"], align_right),
            (d["elo_b_depois"], align_right),
            (d["delta_elo"], align_right)
        ]
        for col_idx, (val, alignment) in enumerate(cells, start=1):
            c = ws_duelos_palestras.cell(row=row_idx, column=col_idx, value=val)
            c.fill = fill
            c.font = regular_font
            c.alignment = alignment
            c.border = grid_border

    # ==========================================
    # ABA 6: Resumo Executivo
    # ==========================================
    ws_kpi = wb.create_sheet(title="Resumo_Executivo")
    ws_kpi.views.sheetView[0].showGridLines = True

    ws_kpi.cell(row=1, column=1, value="📊 Painel Executivo - Mercado em Conexão").font = title_font
    ws_kpi.cell(row=2, column=1, value=f"Gerado em: {now_str}").font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    stats = get_stats()
    kpis = [
        ("Total de Estudantes Inscritos", stats.get("total_inscritos", 0)),
        ("Total de Participantes nos Duelos", stats.get("total_participantes", 0)),
        ("Total de Duelos Realizados", stats.get("total_duelos", 0)),
        ("Duelos de Brindes", stats.get("duelos_brindes", 0)),
        ("Duelos de Palestras", stats.get("duelos_palestras", 0)),
        ("Brinde Líder Atual", stats.get("brinde_lider", "N/A")),
        ("Pontuação Elo do Brinde Líder", stats.get("brinde_lider_elo", 1000.0)),
        ("Palestra Líder Atual", stats.get("palestra_lider", "N/A")),
        ("Pontuação Elo da Palestra Líder", stats.get("palestra_lider_elo", 1000.0)),
    ]

    ws_kpi.cell(row=4, column=1, value="Indicador").fill = accent_fill
    ws_kpi.cell(row=4, column=1).font = accent_font
    ws_kpi.cell(row=4, column=1).border = grid_border

    ws_kpi.cell(row=4, column=2, value="Valor").fill = accent_fill
    ws_kpi.cell(row=4, column=2).font = accent_font
    ws_kpi.cell(row=4, column=2).alignment = align_center
    ws_kpi.cell(row=4, column=2).border = grid_border

    for row_idx, (lbl, val) in enumerate(kpis, start=5):
        fill = zebra_fill if row_idx % 2 == 0 else white_fill
        c1 = ws_kpi.cell(row=row_idx, column=1, value=lbl)
        c1.fill = fill
        c1.font = bold_font
        c1.border = grid_border

        c2 = ws_kpi.cell(row=row_idx, column=2, value=val)
        c2.fill = fill
        c2.font = regular_font
        c2.alignment = align_center
        c2.border = grid_border

    # Ajuste automático da largura das colunas em todas as abas
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                # Evita medir o título que fica mesclado ou longo na linha 1
                if cell.row > 2 and len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
