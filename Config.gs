const CONFIG = {
  SPREADSHEET_ID: '1GU-sdMPBQELhPauazH4lyeZfxTcmA8mTBpt9pyj0hqA',
  ABAS: {
    ITENS: 'Torneio_Itens',
    RESPOSTAS: 'Torneio_Respostas',
    PARTICIPANTES: 'Torneio_Participantes'
  }
};

function getPlanilha() {
  return SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
}