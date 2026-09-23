# Demo ao vivo, perguntas da banca e checklist

---

## Antes de apresentar: corrigir ou ter resposta

Encontrei estes pontos ao revisar o código para a apresentação. Os itens 1 e 2 já foram corrigidos; o **2b** ainda quebra o painel nesta máquina.

| # | Onde | Problema | O que fazer |
| --- | --- | --- | --- |
| 1 | `painel/templates/painel/dashboard.html`, gráfico "Top 3" | Usava `l.curso__nome_curso`, mas a métrica devolve a chave **`nome`**: rótulos vazios. | ✅ Corrigido (commit `782277c`, branch `front/animacoes`). |
| 2 | Mesmo gráfico | Total suprimido (< 5) virava **`None`** no JavaScript → `ReferenceError` → nenhum gráfico desenhava. | ✅ Corrigido no mesmo commit: suprimidos ficam fora do gráfico. **Só funciona depois do merge do PR de `front/animacoes`.** |
| 2b | MySQL da máquina da demo | `core.tests` falha: as **tabelas de fuso** estão vazias, e aí todo filtro por período do painel volta vazio, sem erro. | Carregar `timezone_posix.sql` (README, seção "Tabelas de fuso") **antes** da demo. |
| 3 | Mesmo arquivo | Estilos inline e cores fixas fogem do padrão de tokens do resto do front. | Se não der tempo de mover para `painel.css`, **não abra esse arquivo** na parte de front. Mostre `quiz.html` e `resultado.html`. |
| 4 | `base.html` | O `acessibilidade.js` existe, mas nenhum botão `data-alternar` está na tela. | Adicionar os botões ou não prometer o recurso. |
| 5 | `quiz/views.py` e `templates/quiz/dashboard.html`, `templates/quiz/curso_detalhe.html` | Código do dashboard antigo, **sem rota** (`/quiz/dashboard/` só redireciona para `/painel/`). | Resposta pronta: "é legado da primeira versão; o painel novo substituiu e o endereço antigo redireciona com 301. Fica como limpeza pendente." |
| 6 | `quiz/engine.py` | A função se chama `recomedacao` (erro de digitação) e existe uma `banda()` que não é usada. | Não é bug, mas alguém pode notar. Admita como débito técnico. |

> Rode `python manage.py test` **depois** de qualquer correção e antes de sair de casa.

---

## Roteiro da demo (5 min)

**Preparação (na véspera):**

```bash
cd backend
python manage.py migrate
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes
python manage.py createsuperuser        # conta da coordenação
python manage.py runserver
```

Responda o quiz **pelo menos 5 vezes** (perfis diferentes). Senão o painel mostra só o total, que é o comportamento correto de privacidade mas não impressiona. Deixe também uma conta de aluno criada.

**Na hora, duas janelas lado a lado:** a normal (coordenação logada) e uma **anônima** (aluno).

| Passo | Tela | O que falar |
| --- | --- | --- |
| 1 | `/painel/` (coordenação) → **Gerar link** | "A coordenação gera um link com token UUID para distribuir na escola." |
| 2 | Cola o link na janela anônima | "O token vai para a sessão; a tentativa sai marcada como 'via link'." |
| 3 | Responde o quiz **com o teclado** e depois com o mouse | Barra de progresso, avanço automático, Enter, foco. "Sem JS isso tudo funciona pelo `#` da URL." |
| 4 | Tela "Analisando" → **Resultado** | Anel de afinidade, "Por que este curso?" (a **explicação** da engine), outros cursos com barras. |
| 5 | **Salvar** um curso sem estar logado | Vai para o login e, ao entrar, o curso já está salvo: interesse pendente + signal que adota a tentativa anônima. |
| 6 | `/lista_interesse/` e `/meus-testes/` | Snapshot: posição e afinidade do momento em que salvou. |
| 7 | Volta ao `/painel/` | Números atualizados, período 30/90/365, "—" onde a contagem é < 5. **Fecha o link** e mostra que ele passa a dar "link inválido". |

Plano B: grave um vídeo curto da demo funcionando e deixe prints no slide. Se o MySQL ou a rede falhar, você segue.

---

## Perguntas prováveis da banca (com resposta curta)

### Sobre a engine

**Por que similaridade de cosseno?**
Porque compara o *formato* do perfil, não a intensidade. Dois alunos com as mesmas preferências relativas recebem a mesma recomendação, mesmo que um tenha marcado pesos maiores. E o resultado já sai entre 0 e 1, pronto para virar porcentagem.

**Por que não usar machine learning ou IA?**
Não há dados históricos rotulados (quem fez qual curso e se deu certo) para treinar. O cosseno é **explicável**, **determinístico** e **auditável** pela coordenação: dá para dizer exatamente por que um curso apareceu. IA fica como evolução futura, para escrever o texto da explicação, por exemplo, não para decidir o ranking.

**De onde vêm os pesos?**
Foram definidos pelo grupo com base no catálogo (12 áreas, 20 cursos, 73 pesos, nos seeds) e são editáveis pelo admin. Validar os pesos com orientadores da escola é um próximo passo.

**O que é a "confiança"?**
É o quanto o 1º colocado se separou do 2º, em relação ao 1º. Abaixo de 5% é "baixa" e o sistema avisa o aluno em vez de fingir certeza.

**E se der empate?**
A confiança sai "baixa" e o aviso aparece. O campo `tie_set` existe no model para registrar empates, mas ainda não é preenchido. Fale isso como limitação.

### Sobre o backend

**Por que Django com templates e não API + React?**
O projeto começou com React e migrou. Com templates há um deploy só, nenhuma API pública para proteger, sessão e CSRF nativos, e o quiz funciona sem JS. O `djangorestframework` continua instalado caso uma API seja necessária no futuro.

**Como evitam que alguém veja o resultado de outra pessoa?**
Tentativa com dono só o dono vê; tentativa anônima só no navegador que respondeu (o id fica na sessão). Fora disso é 404, que não revela se o id existe. A regra está num lugar só (`quiz/permissoes.py`) e tem teste.

**E se o aluno responder anônimo e depois criar conta?**
O signal `user_logged_in` adota as tentativas que estão na sessão daquele navegador e ainda não têm dono.

**Como garantem consistência ao salvar o quiz?**
Tentativa, respostas e recomendações são gravadas dentro de `transaction.atomic()`. Se a engine falhar, nada fica pela metade.

**E performance?**
`select_related`/`prefetch_related` para evitar N+1, `bulk_create` para respostas e recomendações, índices em `criado_em` e `(rank, curso)` para o painel. Com 20 cursos o cálculo é instantâneo; com 180 cursos (a escala do SENAI) continua linear.

**Como tratam LGPD no painel?**
k-anonimato com k = 5: com menos de 5 tentativas no período, só o total aparece; qualquer contagem menor que 5 vira "—", e a taxa correspondente também é escondida para não deixar deduzir o número. Nenhum nome ou e-mail aparece no painel.

**Qual a cobertura de testes?**
64 testes cobrindo engine (inclusive isolada do banco), rotas, controle de acesso, lista de interesse, adoção de tentativa, métricas e privacidade.

### Sobre o front

**O que acontece sem JavaScript?**
O quiz funciona: cada pergunta é um `#questao-N` e o CSS `:target` mostra a da vez. O JS só adiciona avanço automático, Enter, foco e a tela "Analisando".

**Como pensaram acessibilidade?**
HTML semântico, navegação por teclado com foco gerenciado, ARIA onde falta semântica, respeito a "reduzir movimento" e tokens prontos para fonte grande e alto contraste.

**Por que CSS puro e não Bootstrap ou Tailwind?**
O protótipo tinha uma identidade própria. Com tokens em CSS puro o resultado é leve, sem build e fiel ao design, e o tema de alto contraste é só outro conjunto de valores.

### Perguntas "armadilha"

- **"Isso é um sistema de recomendação de verdade?"** Sim: é uma recomendação *baseada em conteúdo* (content-based), com perfil e itens no mesmo espaço vetorial. Não é *filtragem colaborativa*, que exigiria histórico de outros usuários.
- **"O que vocês fariam diferente?"** Validar os pesos com especialistas, remover o código legado, cobrir o painel com teste de template e medir a aceitação real (quantos alunos se matricularam no curso recomendado).

---

## Limitações e próximos passos (slide final)

1. Pesos definidos pelo grupo, ainda sem validação empírica.
2. Empate registrado só pela confiança (`tie_set` ainda vazio).
3. Código legado do dashboard antigo a remover.
4. Integração com o sistema de matrícula (SGSET) e trilha de cursos: fora do escopo atual.
5. Camada de IA para gerar a explicação em linguagem natural: proposta, não implementada.

---

## Checklist da véspera

- [x] Itens 1 e 2 da tabela do topo corrigidos (gráficos do painel)
- [ ] PR de `front/animacoes` mergeado (ou apresentar a partir dessa branch)
- [ ] `python manage.py test` → **OK** (print no slide)
- [ ] Banco com seeds + ≥ 5 tentativas + 1 superusuário + 1 aluno
- [ ] Tabelas de fuso do MySQL carregadas (`python manage.py test core`)
- [ ] Demo ensaiada do começo ao fim **cronometrada**
- [ ] Vídeo ou prints de backup
- [ ] Cada integrante sabe explicar a parte que escreveu **e** a engine
- [ ] Conta à mão do cosseno pronta num slide
- [ ] Zoom do navegador e do editor em 125–150% (o projetor não perdoa)
- [ ] Abas abertas na ordem: `models.py` → `engine.py` → `web_views.py` → `privacidade.py` → `quiz.html` → `quiz.js`
