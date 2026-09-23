# Serviço de análise de menções de marcas em respostas de IA
## Sobre o projeto
Este projeto visa ser uma API que provém o serviço de análise de menções de marcas em respostas geradas por modelos generativos (LLMs).

## Arquitetura do projeto
O projeto é dividido em três camadas:
- App: aplicação FastAPI para servir as análises de menções
- Data_manager: camada de limpeza, normalização e gestão dos dados para a persistência no banco
- Tests: camada de realização de testes do projeto