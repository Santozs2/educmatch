---
title: "Spec · Catálogo real do SENAI: cursos, pesos, áreas e quiz (EDU-207)"
aliases: ["Catálogo real", "EDU-207", "Cursos SENAI", "Pesos dos cursos"]
tags: [tcc, spec, catalogo, quiz, dados, senai]
status: proposto
projeto: TCC
branch: feat/catalogo-senai
criado: 2026-11-02
---

> [!info] Contexto: planilhas em `Documents/educmatch_web_scraping` · Pesos para revisão: `docs/catalogo-senai/pesos-cursos-senai-v1.xlsx` · Depende de: `feat/peso-area-curso`

# Spec: catálogo real do SENAI (EDU-207)

> [!abstract] O que esta spec resolve
> Hoje o sistema recomenda 20 cursos fictícios, com 12 áreas que não batem com o catálogo do SENAI. Esta spec troca isso por **50 cursos reais da unidade 801**, com **10 áreas do SENAI**, um **quiz novo** e o **detalhe do curso** com as informações reais. O histórico dos alunos continua intacto.

## 1. Decisões

| # | Decisão | Motivo |
|:-:|---|---|
| D1 | As áreas passam a ser as do SENAI (10) | Curso e quiz precisam medir a mesma coisa |
| D2 | O quiz é reescrito, como versão 2 | O quiz atual pesa nas áreas antigas, e só `ti` continua |
| D3 | Nada é apagado: cursos, áreas e perguntas antigos ficam inativos | `Recomendacao` e `Resposta` usam `CASCADE`, então apagar eliminaria o histórico. Curso com interesse ou link de avaliação está em `PROTECT` e nem poderia ser apagado |
| D4 | O curso é identificado pelo código do link do SENAI | "Assistente Administrativo" tem dois cursos com o mesmo nome |
| D5 | Os 3 cursos sem descrição entram inativos (7, 35 e 46) | A regra 4 do prompt só permite à IA afirmar o que está na descrição |
| D6 | Os dados ficam em CSV no repositório | É versionado, entra no pacote de deploy e não exige `openpyxl` em produção |
| D7 | Aprendiz SENAI e Graduação mostram **"Ver no site do SENAI"** no lugar de "Inscrever-se" | Evita prometer uma inscrição direta que talvez não exista. Falta confirmar com a escola (§8) |

## 2. Modelo de dados

**`Curso`** (migração `catalogo/0002`):

| Campo | Definição | Uso |
|---|---|---|
| `nome_curso` | `max_length=150` | Já alterado na árvore de trabalho, **sem commit e sem migração** |
| `codigo_senai` | `CharField(max_length=20, unique=True, null=True, blank=True)` | Chave da importação. Número final do link |
| `nivel` | `choices`: `livre`, `aprendiz`, `graduacao`. Padrão `livre` | Etiqueta e texto do botão |
| `modalidade` | `CharField(max_length=30, default="Presencial")` | Etiqueta |
| `unidade_carga` | `choices`: `horas`, `horas_aula`. Padrão `horas` | "2880 horas/aula" no curso 32 |
| `url_senai` | `URLField(blank=True, max_length=300)` | Destino do botão |
| `consultado_em` | `DateField(null=True, blank=True)` | Linha de procedência |

**`Area`**: `is_active = BooleanField(default=True)`.

**`Questao`** (migração `quiz`): `versao = PositiveSmallIntegerField(default=1)`.

## 3. Dados e migração

### 3.1 CSV

Arquivo: `backend/catalogo/dados/cursos_senai_801.csv`, em UTF-8, separado por `;`. É gerado uma vez a partir da planilha **depois da revisão**. A planilha fica em `docs/` como registro.

```
codigo_senai;nome;descricao;area;nivel;modalidade;duracao;unidade_carga;url;consultado_em;ativo;pesos
108288;Eletricista Instalador Predial;O curso de...;automacao-energia;livre;Presencial;160;horas;https://...;2026-10-30;1;automacao-energia=5|construcao-mobiliario=2
```

- Curso inativo tem `descricao` vazia. O texto provisório da planilha **não** entra.
- O curso 7 não tem link, então fica com `codigo_senai` vazio e é localizado pelo nome.
- Antes de gerar o CSV, conferir a data de consulta de cada planilha. A página 1 diz 30/10/2026.

### 3.2 Inativar o catálogo antigo

Migração de dados em `catalogo/0003`, reversível:

- Inativa os 20 cursos fictícios, com os nomes escritos na própria migração, e não só os que o seed deixa de listar.
- Inativa 11 áreas: `costura`, `eletrica`, `eletromecanica`, `financas`, `ia`, `marketing`, `mecanica`, `mecanica-automotiva`, `metalurgia`, `rh` e `design`. O slug `ti` continua.

### 3.3 `seed_areas`

Passa a listar só as 10 áreas novas, com `is_active=True`.

| Slug | Nome |
|---|---|
| `automacao-energia` | Mecatrônica, Sistemas de Automação, Energia e Eletrônica |
| `ti` | Tecnologia da Informação e Informática |
| `automotiva` | Automotiva |
| `fabricacao-mecanica` | Fabricação Mecânica e Manutenção Industrial |
| `metalurgia-soldagem` | Metalurgia e Soldagem |
| `administracao-gestao` | Administração e Gestão |
| `refrigeracao-climatizacao` | Refrigeração e Climatização |
| `logistica-transporte` | Logística e Transporte |
| `construcao-mobiliario` | Construção Civil e Design de Mobiliário |
| `moda-joalheria` | Design de Moda, Têxtil, Vestuário, Calçados e Joalheria |

### 3.4 `seed_cursos`

Passa a ler o CSV, e a lista `CURSOS` do arquivo sai.

- Mantém a regra da `feat/peso-area-curso`: curso que já existe não é alterado, porque a edição do painel vale mais. Sem isso, cada deploy desfaz a revisão.
- Procura por `codigo_senai`, ou pelo nome quando o código está vazio.
- O `is_active` vem da coluna `ativo`. **Hoje o código força `True`**, e com `--sobrescrever` isso reativaria os cursos sem descrição.
- Para de falhar em silêncio: área desconhecida, peso fora de 0 a 5 ou área principal sem ser o maior peso geram `CommandError`.

Adicionar cursos depois, como os 2 da página 6, é só incluir linhas no CSV.

### 3.5 `seed_questoes`

> [!danger] Armadilha do seed atual
> O seed localiza a pergunta pelo texto e apaga as alternativas que saíram do arquivo. A exclusão passa por `Resposta` em `CASCADE`. Como as 10 perguntas novas reaproveitam o texto das antigas, e só 10 das 40 alternativas continuam iguais, rodar o seed novo sem esta mudança **apagaria respostas de alunos**.

- `VERSAO_QUIZ = 2`. A busca passa a ser por `(texto, versao)`.
- Ao final: `Questao.objects.exclude(versao=VERSAO_QUIZ).update(is_active=False)`.
- As perguntas e alternativas da versão 1 ficam como estão.
- Regra para o futuro: mudar o texto de uma alternativa depois que houver respostas exige subir `VERSAO_QUIZ`. Deixar isso em comentário no arquivo.

O conteúdo do quiz está na aba **Quiz** da planilha.

## 4. Telas

### 4.1 Detalhe do curso (`curso_detalhe.html`)

| Informação | Como aparece |
|---|---|
| Área, nível e modalidade | Etiquetas |
| Carga horária | Etiqueta com a unidade certa: `get_unidade_carga_display` |
| Descrição | Sem mudança |
| Procedência | "Informações do site do SENAI, consultadas em 30/10/2026. Confirme as turmas na inscrição." Só quando `consultado_em` existe |
| "Início em" | Sem mudança: o curso real não tem data, então a etiqueta não aparece |

**Não aparecem:** número no catálogo, página, URL de origem, unidade, status de verificação e observações.

### 4.2 Botão de inscrição

- `url_curso_senai` devolve `curso.url_senai` quando existir. Sem link, continua na busca atual.
- O texto muda por nível nas três telas que usam o link: detalhe, resultado e redirecionamento de "Manifestar interesse". Fica numa propriedade só, `Curso.aceita_inscricao_direta`.

### 4.3 Cursos inativos no histórico

> [!warning] Quebra sem esta correção
> `curso_detalhe` responde 404 para curso inativo. Depois da troca, **todo resultado antigo e toda lista de interesse** teriam links quebrados.

Em `resultado.html`, `accounts/lista.html` e `aluno_perfil.html`: curso inativo mostra o nome **sem link e sem botão de inscrição**, com o aviso "Curso não oferecido atualmente".

### 4.4 Painel

- `NovoCurso`: incluir `nivel`, `modalidade`, `unidade_carga` e `url_senai`. `codigo_senai` fica fora.
- Listas de área em `NovoCurso` e `PesoCursoForm`: só áreas ativas, mantendo a área atual de um curso antigo.
- `Cursos e Áreas` e `cobertura_de_areas`: só áreas ativas.
- `demanda_por_area` continua lendo todas, porque o histórico cita as áreas antigas.
- Curso inativo não aparece no painel: os cursos 7, 35 e 46 são completados e reativados pelo admin do Django, que exige a descrição.

## 5. Pesos: como foram feitos e o que a simulação mostrou

**Regras:** a área principal é a do SENAI e recebe 5, sempre o maior peso. Área secundária (1 a 3) só entra com base na descrição, registrada na coluna Motivo. Exceções marcadas na planilha: os cursos 7, 35 e 46 têm peso só pelo nome, e o Excel Básico (11) tem ADM por inferência.

**Simulação** com o mesmo cálculo do motor, top 5, em 47 cursos ativos e 20.000 perfis de respostas sorteadas:

| Medida | Resultado | Leitura |
|---|---|---|
| Cursos que nunca chegam ao top 5 | **0** | Todo curso aparece para alguma combinação de respostas |
| Cursos com menos de 1% de presença no top 5 | **4** (27, 29, 34 e 50) | Existem, mas raramente aparecem |
| Cursos quase nunca em 1º (menos de 0,1%) | **18** | Muitos só aparecem nas alternativas |
| Grupos com pesos idênticos | **9 grupos, 23 cursos** | Empatam sempre, e a ordem sai do nome do curso |
| Perfis com empate no 1º lugar | **50,8%** | Em metade dos perfis a IA pode escolher o principal |
| Mediana da afinidade do 1º lugar | **0,69** | Banda "média" |
| Curso mais frequente em 1º | **32, Mecatrônica: 13,2%** | Tem 3 áreas, então combina com perfis mistos. É graduação de 2880 horas/aula |

> [!warning] Limites desta medição
> Respostas sorteadas não representam alunos reais, que tendem a ser mais coerentes. A simulação aponta riscos, mas não prevê a qualidade da recomendação. Isso só a avaliação humana mede.

**Limites do catálogo:**

- Moda e Construção têm 1 curso cada, e Refrigeração tem 2. Quem tem esse perfil recebe logo em seguida cursos de outras áreas, com afinidade bem menor.
- Dez áreas não distinguem cursos parecidos. Os 5 cursos de IA só com TI (12, 16, 17, 23 e 27) são iguais para o motor. Criar subáreas resolveria, mas deixaria de ser a classificação do SENAI. **Fica fora desta spec**, e a revisão pode reduzir empates ajustando pesos que tenham base.

## 6. Testes

**Novos:**

- CSV: 50 cursos, 47 ativos, sem o texto provisório em nenhuma descrição, código único e área principal sempre com o maior peso.
- Seed rodado duas vezes não duplica nada e não desfaz edição do painel.
- `--sobrescrever` não reativa curso sem descrição.
- **Seed novo sobre banco com a versão 1 não apaga nenhuma `Resposta`.** Só as perguntas da versão 2 ficam ativas.
- Migração inativa os 20 cursos e as 11 áreas, sem apagar `Recomendacao`.
- Resultado antigo com curso inativo abre sem link para 404.
- Detalhe mostra nível, modalidade e "horas/aula". Botão usa `url_senai`, ou a busca quando não há link.
- Aprendiz e Graduação mostram "Ver no site do SENAI".
- Toda área ativa tem alternativa no quiz e curso ativo.

**Ajustar:** os testes que dependem do catálogo antigo: `catalogo/tests.py`, `painel/tests/test_metricas.py`, `painel/tests/test_telas.py`, `painel/tests/test_avaliacoes.py`, `quiz/tests/test_engine_puro.py`, `quiz/tests/test_llm_entrega_v1.py` e `quiz/tests/test_resultado.py`. Onde o teste não trata do catálogo, criar os dados no próprio teste, para não voltar a depender do seed.

Rodar a suíte com o `RunnerSemRede`, como hoje.

## 7. Ordem e deploy

1. Fazer o merge de `feat/peso-area-curso` na `develop`. Ela ainda não foi enviada para o GitHub.
2. Commitar a mudança de `nome_curso` já com a migração.
3. Criar `feat/catalogo-senai` a partir da `develop`, com commits nesta ordem: modelo → CSV e seeds → telas → painel → testes.
4. **Só gerar o CSV final depois da revisão dos pesos.** Até lá, usar a v1 para desenvolver.
5. Antes do deploy, copiar `/home/data/educmatch.sqlite3`.
6. Publicar fora de horário de uso: quem estiver no meio do quiz antigo pode perder o preenchimento.
7. Conferir em produção: 47 cursos ativos, 10 áreas visíveis, 10 perguntas ativas, resultado antigo abrindo e um quiz completo com link direto do SENAI.

**Rollback:** restaurar a cópia do banco e reverter a release. A migração reversa reativa o catálogo antigo, mas não remove os cursos novos.

## 8. Fora do código

| Item | Quem | Bloqueia a release? |
|---|---|---|
| Revisar pesos e quiz na planilha | Grupo e escola | **Sim** |
| Confirmar se as duas "Fabricação Mecânica" são a mesma área | Grupo ou escola | Sim: muda o CSV |
| Confirmar como funciona a inscrição de Aprendiz SENAI e Graduação | Escola | Não: D7 é o padrão seguro |
| Coletar a página 6 (2 cursos) | Luis | Não: entra depois por CSV |
| Completar descrição dos cursos 7, 35 e 46 | Escola | Não: ficam inativos |
| Refazer o experimento da IA no catálogo novo | Grupo | Não para o deploy, **sim para a banca** |

> [!warning] Efeito no TCC
> Os números de `docs/apresentacao/ia.md` §6 e `docs/experimento/*.csv` foram medidos no catálogo fictício. Eles precisam ficar identificados assim, e o experimento e a avaliação humana (EDU-205) devem ser feitos no catálogo novo.

## 9. Fora de escopo

- Trava ou aviso contra peso sem sentido no painel: adiado por decisão do Luis.
- Subáreas para diferenciar cursos parecidos.
- Sugestão de pesos por IA.
- Datas e vagas de turmas: as planilhas não têm.
- Atualização automática do catálogo a partir do site do SENAI.
