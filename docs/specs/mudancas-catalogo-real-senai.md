---
title: "O que mudou · Catálogo real do SENAI (EDU-207)"
aliases: ["Mudanças EDU-207", "O que mudou no catálogo real"]
tags: [tcc, spec, catalogo, quiz, mudancas]
status: implementado-sem-release
projeto: TCC
branch: feat/catalogo-senai
criado: 2026-11-02
---

> [!info] Contexto: plano original em [[spec-catalogo-real-senai]] · Esta página descreve o que foi **feito**.

# O que mudou: catálogo real do SENAI

> [!abstract] Resumo
> O sistema trocou os 20 cursos fictícios por 50 cursos reais do SENAI (47 ativos), passou a usar as 10 áreas do SENAI e ganhou um quiz novo. Nada do histórico é apagado: o que é antigo fica inativo.
>
> **Situação:** na `develop`, sem deploy. Os pesos e o quiz são a primeira versão e **ainda não têm revisão da escola**.

## 1. Antes e depois

| | Antes | Agora |
|---|---|---|
| Cursos | 20 fictícios, escritos no código | 50 reais, lidos de um CSV (47 ativos) |
| Áreas | 12, como Costura, RH e Marketing | 10 do SENAI. Só o slug `ti` continua |
| Quiz | 10 perguntas sobre as áreas antigas | 10 perguntas sobre as áreas novas (versão 2) |
| Botão do curso | Abria uma busca no site do SENAI | Abre a página do curso. A busca fica só para curso sem link |
| Curso antigo no histórico | Link funcionava | Aparece sem link, com "Curso não oferecido atualmente" |

## 2. Banco de dados

### Campos novos

| Tabela | Campo | Para que serve |
|---|---|---|
| `Curso` | `codigo_senai` | Identifica o curso. O nome não serve, porque há dois "Assistente Administrativo" |
| `Curso` | `nivel` | Cursos Livres, Aprendiz SENAI ou Graduação |
| `Curso` | `modalidade` | Hoje todos são Presencial |
| `Curso` | `unidade_carga` | `horas` ou `horas/aula` |
| `Curso` | `url_senai` | Destino do botão |
| `Curso` | `consultado_em` | Data mostrada na tela |
| `Area` | `is_active` | Esconde área antiga sem apagar |
| `Questao` | `versao` | Separa o quiz novo do antigo |

Além disso, `Curso.nome_curso` passou de 100 para 150 caracteres.

### Migrações

| Migração | O que faz |
|---|---|
| `catalogo/0002_campos_do_catalogo_senai` | Cria os campos do catálogo |
| `catalogo/0003_inativa_catalogo_ficticio` | Inativa os 20 cursos fictícios e 11 áreas antigas |
| `quiz/0007_questao_versao` | Cria o campo `versao` |

> [!warning] A migração não traz os cursos novos
> Ela só inativa os antigos. **Sem rodar os seeds depois, o sistema fica sem nenhum curso ativo.**

## 3. Seeds

- **`seed_areas`:** cria as 10 áreas do SENAI.
- **`seed_cursos`:** lê `backend/catalogo/dados/cursos_senai_801.csv`.
  - Curso que já existe não é alterado, para o deploy não desfazer edições do painel.
  - Para com erro se o CSV tiver peso inválido, área inexistente ou área principal sem o maior peso.
- **`seed_questoes`:** cria o quiz versão 2 e inativa as perguntas de outras versões. As perguntas antigas continuam no banco, porque são as respostas do histórico.

> [!danger] Regra para o futuro
> Depois que houver respostas, não edite o texto de uma alternativa no seed: isso apaga as respostas dela. Suba `VERSAO_QUIZ`.

## 4. Telas

**Detalhe do curso**
- Novas etiquetas: nível e modalidade.
- Carga na unidade certa, como "2880 horas/aula".
- Nova linha: "Informações do site do SENAI, consultadas em 30/10/2026. Confirme as turmas na inscrição."

**Botão de inscrição**
- Cursos Livres: "Inscrever-se".
- Aprendiz SENAI e Graduação: "Ver no site do SENAI", até a escola confirmar como é a inscrição.

**Resultado, Minha Lista e Perfil**
- Curso inativo aparece sem link e sem botão de inscrição.
- Na Minha Lista e no Perfil, toda linha segue o mesmo padrão: título e descrição em cima, etiquetas embaixo e "Remover" à direita.
- Descrições limitadas a 30 palavras nos cartões e nas listas.
- A etiqueta de área no resultado tem largura limitada, para não espremer o nome do curso.

**Interesse**
- Não é mais possível salvar interesse em curso inativo: a resposta é 404.

**Painel**
- O cadastro de curso ganhou nível, modalidade, unidade da carga e link.
- Áreas inativas saem das listas, mas um curso que já usa uma delas continua com ela na edição.
- A cobertura de áreas considera só áreas e perguntas ativas.

**Admin do Django**
- Mostra os novos campos e filtros. É por ele que se reativam os cursos 7, 35 e 46 depois de completar a descrição.

## 5. Dados que entraram

- **Planilha de revisão:** `docs/catalogo-senai/pesos-cursos-senai-v1.xlsx`.
- **Cursos inativos:** 7 (Deep Learning), 35 (Assistente Administrativo, 400h) e 46 (Assistente Técnico de Vendas), todos sem descrição.
- **Fora do catálogo:** os 2 cursos da página 6, que não foram coletados.

## 6. Como foi testado

| Verificação | Resultado |
|---|---|
| Suíte em SQLite | 282 testes, 1 erro esperado (`FusoDoMySQL`, que só funciona em MySQL) |
| Atualização de banco com dados antigos, em SQLite | 47 cursos ativos, 10 áreas e 10 perguntas, sem perda de respostas, recomendações ou interesses |
| Navegador, em desktop e em 375 px | Resultado, detalhe e resultado antigo sem estouro de largura |

**Não testado:** a suíte e as migrações em MySQL, que é o banco local; o modal do painel no navegador; o resultado com a IA ligada; e o deploy.

## 7. Como rodar localmente

Na pasta `backend`, com a `.venv` ativa:

```bash
python manage.py migrate
```

```bash
python manage.py seed
```

```bash
python manage.py runserver
```

`makemigrations` não é necessário: as migrações já estão no código.

**Para conferir:** refaça o quiz, veja os cursos reais no resultado e abra o detalhe de um deles. Uma tentativa feita antes da troca deve abrir com "Curso não oferecido atualmente".

**Para desfazer:** restaure uma cópia do banco. Reverter as migrações não basta: os cursos novos continuam no banco e as perguntas antigas não voltam a ficar ativas.

## 8. O que falta

1. Revisar pesos e quiz com a escola.
2. Confirmar se as duas "Fabricação Mecânica" são a mesma área.
3. Gerar o CSV final a partir da planilha revisada.
4. Abrir a release da `develop` para a `main`.
5. Copiar o banco de produção antes do deploy.
6. Refazer o experimento da IA e a avaliação humana no catálogo novo.
