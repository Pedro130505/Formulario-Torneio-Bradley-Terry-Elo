function doGet(e) {
  const canal = (e && e.parameter && e.parameter.canal)
    ? String(e.parameter.canal).trim()
    : 'geral';

  const template = HtmlService.createTemplateFromFile('Index');
  template.canal = canal || 'geral';

  return template.evaluate()
    .setTitle('Pesquisa de Favoritismo')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}