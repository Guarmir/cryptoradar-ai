# 🚀 CryptoRadar AI

CryptoRadar AI é uma API de análise de criptomoedas que transforma dados de mercado em **sinais claros de oportunidade**, com foco em estabilidade, performance e experiência real de usuário.

> Projeto construído passo a passo com arquitetura pronta para produção e lojas de aplicativos.

---

## 🎯 O que o projeto faz

- Consulta preços de criptomoedas em tempo real
- Calcula um **score de oportunidade (0–100)**
- Interpreta o score com sinais claros (🟢 🟡 🔴)
- Possui **cache com fallback** para evitar rate limit
- Funciona em produção com frontend web e base mobile

---

## 🧠 Como o Score funciona

O score é calculado usando:

- Variação de preço em 24h
- Volume negociado
- Market cap
- Tendência do preço no dia
- Volatilidade

### Interpretação:
- **70–100** → 🟢 Forte oportunidade
- **40–69** → 🟡 Neutro / observar
- **0–39** → 🔴 Fraco / risco alto

> ⚠️ Este projeto não faz recomendações financeiras.

---

## 🛠️ Tecnologias utilizadas

- Python 3
- FastAPI
- Uvicorn
- CoinGecko API
- Cache em memória
- CORS habilitado
- Deploy em produção (Render)

---

## 🌍 API em Produção

Base URL:
https://cryptoradar-ai.onrender.com

### Endpoints principais

- Status:
GET /

- Preço:
GET /price/{coin}

- Score:
GET /score/{coin}

- Documentação:
GET /docs

---

## 📁 Estrutura do projeto
cryptoradar-ai/
├── backend/
│   └── app/
│       ├── main.py
│       └── services/
│           ├── price_alert.py
│           └── score.py
├── frontend/
│   └── index.html
├── requirements.txt
└── README.md

---

## 🚧 Próximas etapas

- Frontend mais completo (dashboard)
- Aplicativo mobile (Flutter)
- Histórico de dados
- API Keys e monetização
- Publicação em lojas de aplicativos

---

## 👨‍💻 Status do projeto

✔ Backend estável  
✔ Produção online  
✔ Cache e fallback implementados  
✔ Base pronta para app mobile  

---

## 📌 Aviso legal

Este projeto é educacional e informativo.  
Não constitui recomendação de investimento.
