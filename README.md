# CSDETECTOR

Neste documento, abordaremos a refatoração da ferramenta [CSDETECTOR](https://github.com/Nuri22/csDetector), com o 
objetivo de aprimorar a extração de dados do GitHub. A ferramenta atual apresenta algumas limitações que afetam sua eficiência e funcionalidade.

Aqui vamos analizar a ferramenta de forma a entender os seus módulos de forma idependente
e facilitar a refatoração da ferramenta para atitingir o objetivo de melhorar a extração de dados do GitHub.

## Objetivos

Com a refatoração buscamos 3 objetivos principais para entender como sucesso

- [ ] Aceitar múltiplos tokens do GitHub
- [ ] Tratar os possíveis bots que fazem comentários
- [ ] Melhorar a manutenabilidade

Os principais objetivos iniciais da refatoração da ferramenta [CSDETECTOR](https://github.com/Nuri22/csDetector) são os seguintes:

- **Aceitar Múltiplos Tokens do GitHub**: A ferramenta atualmente opera com um único token de autenticação do GitHub. No entanto, para aprimorar a extração de dados e evitar limitações de taxa, é desejável que a ferramenta seja capaz de aceitar e gerenciar múltiplos tokens de autenticação. Isso permitirá uma distribuição mais eficiente das requisições à API do GitHub.
- **Tratar Possíveis Bots que Fazem Comentários**: Durante a análise de repositórios no GitHub, é comum encontrar comentários feitos por bots. Esses comentários podem conter informações irrelevantes ou duplicadas, prejudicando a qualidade dos dados extraídos. O objetivo é implementar mecanismos que identifiquem e filtrem esses comentários, melhorando a precisão e a relevância dos resultados obtidos.
- **Melhorar a Manutenibilidade**: A estrutura e o código da ferramenta devem ser reorganizados e otimizados para melhorar sua manutenibilidade. Isso inclui a divisão clara dos módulos, a adoção de boas práticas de programação, a remoção de código redundante e a documentação adequada do código-fonte. Uma ferramenta bem organizada será mais fácil de entender, modificar e estender no futuro.

### Sobre a CSDETECTOR

**Módulos Principais e Funcionalidades**

- **Módulo de Extração de Métricas:**
  1. **Extração de Artefatos de Desenvolvedores:** Inicia coletando artefatos do sistema de controle de versão.
  2. **Extração de Aliases de Desenvolvedores:** Obtém os aliases (identificadores) dos desenvolvedores.
  3. **Construção de Grafo Social:** Utiliza os aliases para criar um grafo social interconectando os desenvolvedores.
  4. **Cálculo de Métricas Relacionadas a Sentimentos:** Analisa o conteúdo para calcular métricas de sentimento.
  5. **Cálculo de Métricas Sócio-Técnicas:** Utiliza o grafo social para quantificar a colaboração entre os desenvolvedores.

- **Módulo de Detecção de Code Smells:**
  1. **Detecção de Odores na Comunidade:** Utiliza as características extraídas e métricas calculadas como entrada.
  2. **Modelos Pré-Treinados:** Emprega modelos pré-treinados para identificar possíveis "code smells" na comunidade.
  
Esse sistema opera em duas etapas principais: primeiro, ele extrai informações relacionadas aos desenvolvedores e suas interações da comunidade de desenvolvimento; em seguida, ele utiliza essas informações para detectar possíveis problemas ou "Communit Smells".
