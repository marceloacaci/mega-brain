---
tags: [projeto, web, biblioteca-reflexoes, vanilla-js]
---

# Projeto LIVRO — Biblioteca de Reflexões

App web estatico (HTML + CSS + JS vanilla, sem build/framework/backend). Tema Neon Dark Blue. Catalogo de 15 livros com pagina de reflexao por livro (anotacoes em localStorage).

## Estrutura
- index.html — pagina da BIBLIOTECA (grade de 15 cards).
- livro.html — pagina GENERICA de 1 livro (render dinamico via JS).
- css/styles.css — tema completo (~1.4k lin).
- js/books.js — BANCO DE DADOS (window.MEU_BOLSO_BOOKS, 15 livros, ~311 KB).
- js/livro.js — render da pagina do livro.
- js/biblioteca.js — render dos cards na index.html.
- js/app.js — navegacao, filtro, localStorage das reflexoes.
- js/book-theme.js — template base de tema.
- img/ — 15 capas.
- verify-*.js — checagens Node (Node 26 ok).

## 15 livros (id / titulo PT)
ramsey (O Poder da Acao Financeira), fogg (Micro-habitos), kishimi (A Coragem de Nao Agradar), gatilhos (Gatilhos Mentais), menteafiada (Mente Afiada), arrume (Arrume sua Cama), caibalion (O Caibalion), milhonaria (Os Segredos da Mente Milionaria), essencialismo (Essencialismo), greene48 (As 48 Leis do Poder), housel (A Psicologia Financeira), lakhiani (O Buda e o Cara), dispenza (Como Aumentar a Capacidade do Seu Cerebro), kotler (Marketing Empreendedor), kruel (IA e o Novo Profissional Minimamente Viavel).

## Refatoracao data-driven (2026-08-21)
livro.js tinha logica HARDCODED por livro: myths (if/else p/ 15), topicMap e stepLabels (ramsey/fogg). Extraidos para books.js como book.myths, book.topic e book.stepLabels. livro.js agora le book.*. Adicionar livro 16 = editar so books.js. Verificado em browser (0 erros JS; Ramsey 19 cards, Kruel 17 cards, topics corretos).

PENDENTE: buildBabySteps() e buildMicroHabits() em livro.js estao DEFINIDOS MAS NUNCA CHAMADOS (codigo morto). app.js referencia .book-tab/sectionIds inexistentes (filtro inativo).
