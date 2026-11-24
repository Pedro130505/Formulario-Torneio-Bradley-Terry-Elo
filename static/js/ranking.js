/**
 * Interatividade da Página de Ranking: Busca ao vivo e ordenação.
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchRanking');
  const table = document.getElementById('rankingTable');

  if (searchInput && table) {
    searchInput.addEventListener('input', (e) => {
      const termo = e.target.value.toLowerCase().trim();
      const linhas = table.querySelectorAll('tbody tr');

      let visiveis = 0;
      linhas.forEach((linha) => {
        const texto = linha.innerText.toLowerCase();
        if (texto.includes(termo)) {
          linha.style.display = '';
          visiveis++;
        } else {
          linha.style.display = 'none';
        }
      });

      const contadorEl = document.getElementById('contadorFiltrados');
      if (contadorEl) {
        contadorEl.textContent = `${visiveis} itens encontrados`;
      }
    });
  }
});
