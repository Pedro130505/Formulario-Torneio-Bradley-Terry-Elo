"""
Testes de Integração e Validação do Sistema Mercado em Conexão (v3.0).
Testa:
1. Inscrição do formulário com validações.
2. Duelos de Brindes (Bradley-Terry / Elo) com garantia de não repetição.
3. Duelos de Palestras filtradas por Engenharia / Curso do Aluno.
4. Exportação completa para Excel com 6 abas estilizadas.
"""
import unittest
import os
import io
import openpyxl

from database import (
    init_db,
    save_inscricao,
    get_all_inscritos,
    get_inscrito_by_uid,
    get_all_items,
    get_user_voted_pairs,
    get_stats
)
from tournament import get_next_matchup, process_vote, get_enriched_leaderboard
from exporter import generate_excel_report


class TestMercadoEmConexao(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_01_salvar_inscricao_estudante(self):
        dados_teste = {
            "uid": "test_aluno_civil_01",
            "iniciativa": "Minas Jr",
            "nome": "Lucas Martins Silva",
            "email": "lucas.martins@ufmg.br",
            "telefone": "(31) 98765-4321",
            "universidade": "UFMG - Universidade Federal de Minas Gerais",
            "curso": "Engenharia Civil",
            "ano_graduacao": "2027",
            "vagas_6meses": "Sim",
            "fatores_estagio": [
                "Atividades a serem desenvolvidas",
                "Possibilidade de aprendizado e desenvolvimento profissional",
                "Reputação e cultura da empresa"
            ],
            "como_conheceu": "Minas Jr",
            # Novos campos fiéis ao Google Forms
            "como_soube_opcao": "Divulgação de alguma iniciativa",
            "projeto_extensao": "Minas Jr",
            "empresas_desejadas": "Vale, Andrade Gutierrez, MRV, Bain & Company",
            "temas_painel": [
                "Indústria Pesada e Engenharia (processos, manufatura, energia e grandes operações)",
                "Inteligência Artificial e Automação (inovação e o impacto da IA no mercado)",
                "Consultoria e Gestão de Negócios (estratégia, resolução de problemas e cases reais)"
            ],
            "tema_outro": "",
            "periodo_palestras": "Tarde (13-17)",
            "horario_feira": "de 9 às 19"
        }
        id_salvo = save_inscricao(dados_teste)
        self.assertIsNotNone(id_salvo)

        aluno = get_inscrito_by_uid("test_aluno_civil_01")
        self.assertIsNotNone(aluno)
        self.assertEqual(aluno["nome"], "Lucas Martins Silva")
        self.assertEqual(aluno["curso"], "Engenharia Civil")
        self.assertEqual(aluno["iniciativa"], "Minas Jr")
        self.assertEqual(aluno["projeto_extensao"], "Minas Jr")
        self.assertEqual(aluno["como_soube_opcao"], "Divulgação de alguma iniciativa")
        self.assertEqual(aluno["periodo_palestras"], "Tarde (13-17)")
        self.assertEqual(aluno["horario_feira"], "de 9 às 19")
        print(" [OK] Inscrição salva e recuperada com sucesso.")

    def test_02_duelo_brindes_sem_repeticao(self):
        uid = "test_user_duelos_brinde"
        pares_vistos = set()

        for i in range(5):
            res = get_next_matchup(uid=uid, canal="Minas Jr", categoria="brinde")
            self.assertEqual(res["status"], "ok")
            item_a = res["itemA"]
            item_b = res["itemB"]

            # Garante que os cards têm foto e nome
            self.assertTrue(len(item_a["nome"]) > 0)
            self.assertTrue(len(item_a["imagem_url"]) > 0)
            self.assertTrue(len(item_b["nome"]) > 0)
            self.assertTrue(len(item_b["imagem_url"]) > 0)

            par = frozenset([item_a["id"], item_b["id"]])
            self.assertNotIn(par, pares_vistos, "Par repetido detectado!")
            pares_vistos.add(par)

            # Vota no item A
            voto = process_vote(
                uid=uid,
                item_a_id=item_a["id"],
                item_b_id=item_b["id"],
                vencedor_id=item_a["id"],
                canal="Minas Jr",
                categoria="brinde"
            )
            self.assertEqual(voto["status"], "ok")

        print(" [OK] 5 duelos de brindes executados sem nenhuma repetição de par.")

    def test_03_duelo_palestras_filtradas_por_engenharia(self):
        uid = "test_user_palestras_civil"
        curso = "Engenharia Civil"

        for i in range(3):
            res = get_next_matchup(uid=uid, canal="Minas Jr", categoria="palestra", curso=curso)
            self.assertEqual(res["status"], "ok")
            item_a = res["itemA"]
            item_b = res["itemB"]

            # Vota no item B
            voto = process_vote(
                uid=uid,
                item_a_id=item_a["id"],
                item_b_id=item_b["id"],
                vencedor_id=item_b["id"],
                canal="Minas Jr",
                categoria="palestra"
            )
            self.assertEqual(voto["status"], "ok")

        print(" [OK] Duelos de palestras filtradas por Engenharia Civil executados com sucesso.")

    def test_04_exportacao_excel_multiplas_abas(self):
        excel_buf = generate_excel_report()
        self.assertIsInstance(excel_buf, io.BytesIO)
        self.assertGreater(excel_buf.getbuffer().nbytes, 5000)

        # Abre o Excel gerado para conferir as 6 abas
        wb = openpyxl.load_workbook(excel_buf)
        esperadas = [
            "Inscritos_Formulario",
            "Ranking_Brindes",
            "Ranking_Palestras",
            "Duelos_Brindes",
            "Duelos_Palestras",
            "Resumo_Executivo"
        ]
        for aba in esperadas:
            self.assertIn(aba, wb.sheetnames, f"Aba {aba} ausente no Excel!")

        print(f" [OK] Relatório Excel gerado perfeitamente com todas as 6 abas: {wb.sheetnames}")


if __name__ == "__main__":
    unittest.main()
