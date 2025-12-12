Criar um código em python para a criação de uma escala de serviço que possua 8 postos de serviço,
o rodizio entre os postos possa ser atribuído. O nome dos postos são Alfa 2, Ronda P1, Delta 4, Alfa 3, Ronda P2 e P3, Galeria/QAP e  Monitoramento,
o nome dos postos e quantidades, tambem podem ser alterados.
Os postos Alfa 2 e Alfa 3 tem prioridades sobre os demais. Os funcionários que trabalharam nos postos, devem ser alocados, conforme seus horários de trabalho,
devendo ter um equilíbrio sobre os postos de trabalho. Esse código deve usar o banco de dados postgres para a inserção dos dados dos nomes dos postos,
nome dos funcionários bem como a hora de começo e fim da escala do dia. Esse banco deve salvar a escala diariamente, apos ser feita, essa escala deve ficar visivel em um monitor.
O banco deve possuir uma tabela de funcionários, uma de horários de entrada e saída dos funcionários, uma tabela de postos.
O horário de rodizio, dos postos deve ser ajustado(no mínimo 30 minutos e no max. 1 hora)
