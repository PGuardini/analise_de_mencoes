# Serviço de análise de menções de marcas em respostas de IA

## Sumário
- [Sobre o projeto](#sobre-o-projeto)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Arquitetura do projeto](#arquitetura-do-projeto)
    - [Estrutura de pastas](#estrutura-de-pastas)
        - [App](#app)
        - [Data Manager](#data-manager)
        - [Tests](#tests)
    - [Justificativa da estrutura](#justificativa-da-estrutura)
    - [Limites e possibilidades do projeto](#limites-e-possibilidades)

## Sobre o projeto
Este projeto visa ser uma API que provém o serviço de análise de menções de marcas em respostas geradas por modelos generativos (LLMs).

## Como instalar e rodar o projeto
Para ver como fazer instalação e execução do projeto, veja <a href='instalacao.md'>instalacao.md</a>.

## Arquitetura do projeto
### Estrutura de pastas

O projeto é dividido em três camadas:
- `App`: aplicação FastAPI para servir as análises de menções
- `Data_manager`: camada de limpeza, normalização e gestão dos dados para a persistência no banco
- `Tests`: camada de realização de testes do projeto

---

#### APP
A camada App contempla:
- `main.py`: instanciação da API e endpoints dela;
- `models.py`: definição dos modelos de dados utilizados na API para entrada e persistência;
- `services.py`: definição das classes de acesso aos modelos, validam os dados e fazem a mediação entre entrada e persistência dos dados.

#### DATA MANAGER
A camada Data_manager contempla:
- `database.py`: configurações do banco de dados, criação e população do banco, além da disponibilização de uma camada de acesso ao banco via get_session, unificando em um método a geração de sessões;
- `services.py`: definição dos métodos de consumo do arquivo json, de validação e de limpeza de dados, além do método de detecao de marcas.

#### TESTS
A camada Tests contempla:
- `conftest.py`: fixtures compartilhadas entre todos os testes: banco SQLite em memória, isolado por teste e já populado com as três marcas monitoradas, além de um `TestClient` com a dependência `get_session` sobrescrita para usar esse banco isolado ao invés do SQLite real;
- `test_data_manager_services.py`: testes unitários da camada de dados: cobrem validação (`data_validation`), limpeza (`data_cleansing`) e detecção de marcas (`brand_mention_detector`);
- `test_api_services.py`: mistura testes de serviço (`BrandService`, `MentionService`) com testes de ponta a ponta via `TestClient` (fixture `client`), verificando os endpoints reais.

Foi dada prioridade de cobertura para três pontos de maior risco:
1. **Detecção de marcas**, por depender de expressões regulares sensíveis a variações de escrita;
2. **Cálculo de `share-of-voice`, tanto percentual quanto em valores absolutos**, por exigir que toda plataforma apareça no resultado mesmo sem nenhuma menção da marca;
3. **Ranking de `top-citacoes`**, por depender de dois critérios de ordenação (marcas distintas e soma de ocorrências) que só se diferenciam em casos de empate, exigindo um dado de teste desenhado especificamente para forçar esse cenário (`test_ties_in_distinct_brands_broken_by_occurrence_count`).


### Justificativa da estrutura

A estrutura foi pensada buscando isolar a lógica da API da lógica de limpeza, validação e consumo de dados. Além de separar da camada de teste.

A camada `data_manager` busca gerir o banco de dados, disponibilizando uma forma segura de acesso e busca garantir que o banco esteja populado toda vez que a aplicação sobe. 
Ainda, o `data_manager` busca a validação dos dados através do modelo de entrada (`ResponseCreate`) da API, garantindo que, caso o modelo de entrada seja alterado, os dados seguirão sendo validados e seguirão seu fluxo normalmente.

Foi tentado isolar a API de decisões de infraestrutura (tipo de banco e definição da conexão) através da injeção de dependência com o método `get_session()`. Entretanto, `app` e `data_manager` ainda mantém uma dependência mútua em nível de módulo. Isso, com mais tempo, poderia ser resolvido com uma interface de repositório mais explícita.

Os testes de API consomem o app utilizando `TestClient`, o que garante que os mesmos métodos e endpoints da API real estão sendo utilizados.


### Limites e possibilidades

#### Limites do projeto:
- **Interdependência implícita entre camadas**: A lógica de validação dos dados depende dos modelos da API, devido ao consumo de arquivos JSON;
- **Expressões regulares**: As expressões regulares utilizadas se limitam à validação das três marcas informadas no teste, não permitindo a adição de novas marcas para monitorar;
- **Idioma**: A entrada de dados utiliza está em português e converte para o inglês, isso se deve ao fato da escrita do código ter iniciado em inglês e à mistura de idiomas nos endpoints. O ideal seria utilizar apenas um idioma.
- **Conceito de força frágil**: O conceito de força utilizado para calcular o rank do endpoint `top-citacoes` prioriza a quantidade de marcas distintas citadas na resposta, usando a soma de ocorrências textuais de cada marca apenas como critério de desempate.

#### Possibilidades de melhorias futuras:
- **Mudança na forma de detecção de menção à marcas**: foram utilizadas expressões regulares para encontrar as três marcas informadas no teste: Acme, Nimbus e Zenith. Uma possibilidade de melhoria seria utilizar PLN, via spaCy, por exemplo, para detectar marcas (o spaCy cataloga como "ORG" organizações e empresas). Utilizando PLN haveria uma garantia de maior acurácia, pois caso surja alguma nova grafia das marcas, para além do identificado, é possível detectar (coisa que o RegEx utilizado não permite). 
- **Cálculo de força das menções**: seria mais interessante utilizar uma parametrização cruzada utilizando PLN. Assim, combinaríamos o tipo de pergunta e a resposta devolvida, isso partindo da análise do conteúdo dos dados: há perguntas que podem mudar o sentido da resposta, como no registro-exemplo de id `r002`, que já possui uma valoração negativa na pergunta. O cálculo levando em consideração a sintaxe e semântica da língua seria a melhor solução;
- **Melhor modularização e isolamento de camadas**: o projeto tem ainda uma interdependência entre camadas, o que pode gerar problemas futuros na manutenção.