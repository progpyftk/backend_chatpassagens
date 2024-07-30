Projeto Full Stack: Configuração e Arquitetura

Visão Geral do Projeto
O ChatPassagens é um sistema de busca de passagens aéreas que utiliza uma API backend para interagir com diversos serviços de busca de passagens e uma LLM (Large Language Model) como assistente virtual. O objetivo é fornecer uma interface intuitiva e eficiente para os usuários encontrarem as melhores opções de voos, com a assistência de uma inteligência artificial capaz de compreender e responder a consultas complexas.

Este documento descreve a arquitetura e a configuração do nosso projeto full stack, utilizando tecnologias modernas e serviços gerenciados para garantir desempenho e escalabilidade.

## Componentes Principais

1. **Banco de Dados: PostgreSQL (Supabase)**
2. **Cache e Mensageria: Redis (Upstash)**
3. **Frontend: Vue.js com Quasar (Vercel)**

### 1. Banco de Dados: PostgreSQL (Supabase)

Utilizamos o Supabase como provedor de banco de dados PostgreSQL gerenciado, aproveitando sua interface amigável e funcionalidades adicionais. Supabase fornece um banco de dados escalável e seguro, com suporte para extensões como `pgvector` para operações com dados vetoriais.

### 2. Cache e Mensageria: Redis (Upstash)

Upstash é utilizado como nosso serviço de Redis, oferecendo uma solução seporverless otimizada para baixa latência e escalabilidade automática. Este serviço é utilizado para caching e funcionalidades de mensageria em tempo real, integrando-se facilmente com o backend.

### 3. Frontend: Vue.js com Quasar (Vercel)

O frontend da aplicação é desenvolvido com Vue.js e o framework Quasar, proporcionando uma interface de usuário moderna e responsiva. O Vercel é utilizado para hospedar o frontend, oferecendo uma infraestrutura otimizada para deploys contínuos e alta performance.

## Fluxo de Desenvolvimento

- **Backend:** Desenvolvido com Django e Django REST Framework, utilizando o Supabase para persistência de dados e Upstash para caching e mensageria.
- **Frontend:** Construído com Vue.js e Quasar, hospedado no Vercel para fácil deploy e gestão de domínios.

## Hospedagem e Deploy

- **Supabase:** Utilizado para hospedagem do banco de dados PostgreSQL.
- **Upstash:** Utilizado para o serviço de Redis, gerenciando caching e mensageria.
- **Vercel:** Hospeda o frontend, proporcionando CI/CD e deploys rápidos.

Essa configuração garante uma estrutura sólida e escalável para o desenvolvimento de aplicações web modernas, aproveitando o melhor de cada tecnologia.
