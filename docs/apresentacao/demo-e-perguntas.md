---
title: "Apresentação · Demo ao vivo, perguntas da banca e checklist"
aliases: ["Demo e banca", "Perguntas da banca", "Checklist da véspera"]
tags: [tcc, apresentacao, demo, banca, checklist]
status: pronto
projeto: TCC
atualizado: 2026-10-08
---

> [!info] Apresentação: [[README|🎤 Roteiro]] · [[engine|🧮 Engine]] · [[backend|⚙️ Backend]] · [[frontend|🎨 Front]] · [[ia|🤖 Camada de IA]] · **🎬 Demo e banca**

# 🎬 Demo ao vivo, perguntas da banca e checklist

> [!abstract] O que esta nota é
> O roteiro da demo, minuto a minuto; as perguntas mais prováveis, com resposta curta; o que ainda precisa ser corrigido **ou** ter resposta pronta; e o checklist da véspera.

---

## 🔧 1. Antes de apresentar: corrigir ou ter resposta

Pontos encontrados ao revisar o código (atualizado em 2026-10-15):

| # | Onde | O que é | O que fazer |
|:-:|---|---|---|
| 1 | MySQL da máquina da demo | Sem as **tabelas de fuso**, todo filtro por período do painel volta vazio, **sem erro** | Carregar o `timezone_posix.sql` (README, "Tabelas de fuso") e conferir com `python manage.py test core` |
| 2 | `painel/privacidade.py` | `K_MINIMO = 0`: a supressão de números pequenos está **desligada** (decisão de 2026-10-01) | Ter a resposta pronta (§3). **Não** dizer que o painel suprime |
| 3 | `static/js/quiz.js` | A tela "Analisando" segura o envio por **1,5 s** de propósito | Resposta: escolha de experiência; a engine leva milissegundos |
| 4 | Camada de IA | Código pronto (Passos 7 a 11); falta a chave e o experimento | Rodar `testar_llm` no dia; na dúvida, `LLM_ENABLED=0` (ver [[ia|🤖 IA]]) |

> [!success] Já resolvidos desde a última versão desta nota
> `recomedacao` virou **`recomendar`** · a `banda()` foi documentada (fica reservada para o fallback e o tom do prompt da IA; ainda não é chamada) · o **`tie_set` é preenchido** · a régua de empate foi **calibrada** para o quiz de 10 perguntas · os gráficos do painel foram refeitos com `json_script` · os botões de acessibilidade entraram no painel **e no rodapé do aluno** · o código legado do dashboard antigo foi **removido** · o `quiz.js` perdeu as 2 variáveis sem uso · `docs/.obsidian/` saiu do Git.

> [!warning] Rode a suíte depois de qualquer correção
> `python manage.py test` → **209 testes**. Faça isso também antes de sair de casa.

---

## 🎥 2. Roteiro da demo (5 min)

**Preparação, na véspera:**

```bash
cd backend
python manage.py migrate
python manage.py createcachetable
python manage.py seed_areas && python manage.py seed_cursos && python manage.py seed_questoes && python manage.py seed_avaliacao
python manage.py createsuperuser        # conta da coordenação
python manage.py runserver
```

Responda o quiz **várias vezes, com perfis diferentes**, para o painel ter números e o gráfico ter forma. Deixe também uma conta de aluno criada.

**Na hora, duas janelas lado a lado:** a normal (coordenação logada) e uma **anônima** (aluno).

| # | Tela | O que falar |
|:-:|---|---|
| 1 | `/painel/` → **Gerar link** | "A coordenação gera um link com token UUID para distribuir na escola." |
| 2 | Cola o link na janela anônima | "O token vai para a sessão, e a tentativa sai marcada como 'via link'." |
| 3 | Responde **com o teclado** (Tab, setas, Enter) e aponta para a URL | "Cada pergunta é um `#questao-N`. Sem JavaScript, isso tudo funciona." |
| 4 | Tela "Analisando" → **Resultado** | Anel de afinidade e **"Por que este curso?"**: *"esta é a explicação da engine, as áreas que mais pesaram"* |
| 5 | ⭐ **O aviso de empate** | Truque: responda **sempre a 1ª alternativa**. Dá Robô de Soldagem (0,8622) × Caldeireiro (0,8514), a confiança sai **baixa** e o aviso aparece. *"O sistema não finge certeza."* |
| 6 | **Salvar** um curso sem estar logado | Vai para o login e, ao entrar, o curso **já está salvo**: interesse pendente + signal que adota a tentativa anônima |
| 7 | `/lista_interesse/` e `/meus-testes/` | Snapshot: a posição e a afinidade **do momento** em que salvou |
| 8 | `/painel/quiz/` | Distribuição de confiança, cursos em 1º, **taxa de conclusão** e **tempo típico** (mediana) |
| 9 | `/painel/avaliacoes/` → gera link de avaliação → responde na janela anônima | "Anônima **por desenho**: o model não tem onde guardar quem respondeu, nem a hora." Mostra o NPS |
| 10 | **Fecha o link** do quiz | E mostra que ele passa a dar "link inválido" |

> [!tip] Plano B
> Grave um vídeo curto da demo funcionando e deixe prints no slide. Se o MySQL, o Wi-Fi ou o projetor falharem, você segue. O Chart.js vem de CDN: **sem internet, os gráficos não desenham**, mas os números continuam nas legendas.

---

## ❓ 3. Perguntas prováveis da banca

### 🧮 Sobre a engine (as mais importantes)

> [!question] Por que similaridade de cosseno?
> Porque compara o **formato** do perfil, não a intensidade. Dois alunos com as mesmas preferências relativas recebem a mesma recomendação, mesmo que um tenha marcado pesos maiores. E o resultado já sai entre 0 e 1, pronto para virar porcentagem.

> [!question] Por que não usar machine learning ou IA para recomendar?
> Não há histórico rotulado (quem fez qual curso e se deu certo) para treinar. O cosseno é **explicável**, **determinístico** e **auditável**: dá para dizer exatamente por que um curso apareceu. A IA entra para **explicar**, e só pode trocar o 1º lugar onde a engine mostrou empate.

> [!question] De onde vêm os pesos?
> Foram definidos pelo grupo a partir do catálogo (12 áreas, 20 cursos, 73 pesos de curso e 80 de alternativa), estão em seeds reproduzíveis e são editáveis no admin. Validá-los com a coordenação é o próximo passo. A avaliação de fim de curso já pergunta *"o curso combinou com o que o quiz mostrou?"*.

> [!question] O que é a confiança? E o empate?
> É a diferença **absoluta** de afinidade entre o 1º e o 2º: ≥ 0,08 é alta, de 0,02 a 0,08 é média e < 0,02 é **baixa** (empate). No empate a tela avisa o aluno, e o `tie_set` guarda os cursos empatados. A régua de 0,02 foi **calibrada** medindo milhares de perfis com o comando `medir_empate`.

> [!question] Algum curso aparece demais?
> Sim, e nós medimos: em 5.000 perfis sorteados, **Automação Industrial** fica em 1º em 25,7% das vezes, porque tem peso em muitas áreas. As duas especializações de inspeção de solda **nunca** ficam em 1º (mas aparecem no top 5). Os 20 cursos aparecem no top 5 em algum momento. Ajusta-se no admin, mudando pesos.

> [!question] Como sabem que o cálculo está certo?
> Testes automatizados do cosseno sem banco, uma **conta feita à mão** que bate com o sistema (ver [[engine#✏️ 3. Uma conta feita à mão (coloque num slide)|🧮 Engine]]) e uma simulação de 5.000 perfis.

> [!question] E a performance?
> Um ranking dos 20 cursos leva **≈ 0,9 ms**. A recomendação completa faz **12 consultas, sempre**, não importa quantas respostas: `select_related`/`prefetch_related` evitam o N+1. Como o custo cresce **linearmente** com o número de cursos, ainda seria instantâneo com o catálogo inteiro do SENAI.

### 🤖 Sobre a camada de IA

> [!question] O que a IA faz, então?
> Recebe os 5 cursos que a engine escolheu e escreve a explicação em linguagem natural. Só pode trocar o 1º lugar por um curso do `tie_set`. Se falhar, demorar ou responder errado, vale a ordem da engine.

> [!question] E se a internet cair na hora?
> `LLM_ENABLED=0` no `.env` desliga a camada inteira, e o sistema volta a ser só a engine. A engine grava **antes** de qualquer chamada de rede.

> [!question] Vocês mandam dados dos alunos para o Google?
> Não. O payload leva só áreas, cursos e números: nada de nome, e-mail ou usuário. Há um teste que garante isso.

### ⚙️ Sobre o backend

> [!question] Por que Django com templates e não API + React?
> O projeto começou com React e migrou. Com templates há um deploy só, nenhuma API pública para proteger, sessão e CSRF nativos, e o quiz funciona sem JS.

> [!question] Como impedem que alguém veja o resultado de outra pessoa?
> Tentativa com dono, só o dono vê; anônima, só o navegador que respondeu. Fora disso é 404, que não revela se o id existe. A regra está num lugar só (`quiz/permissoes.py`) e tem teste.

> [!question] E se o aluno responder sem conta e criar a conta depois?
> O signal `user_logged_in` adota as tentativas que estão na sessão **daquele navegador** e que ainda não têm dono.

> [!question] Como garantem consistência ao salvar o quiz?
> Tentativa, respostas e recomendações são gravadas dentro de `transaction.atomic()`. Se algo falhar, nada fica pela metade.

> [!question] E a LGPD no painel?
> O painel é restrito à coordenação e **nunca mostra nome nem e-mail**: as métricas não leem `user` nem `respondido_por`, só contam cursos. Construímos o **k-anonimato** (números menores que k viram "—", e a taxa correspondente também some, para não deixar deduzir o número), testamos e deixamos como chave. Para o volume de uma escola, o grupo decidiu mostrar todos os números (`K_MINIMO = 0`). Religar é mudar um número.

> [!question] E a avaliação de fim de curso, é anônima mesmo?
> **Por desenho.** O model não tem campo para usuário, nome, e-mail ou IP, e guarda só o **dia**, não a hora. Não é uma promessa: não há onde guardar.

> [!question] Qual a cobertura de testes?
> **209 testes**: engine (inclusive isolada do banco), empate, `rank_final`, rotas, controle de acesso, lista de interesse, adoção de tentativa, métricas, privacidade e avaliação. A CI roda tudo num MySQL a cada PR.

### 🎨 Sobre o front

> [!question] O que acontece sem JavaScript?
> O quiz funciona: cada pergunta é um `#questao-N` e o CSS `:target` mostra a da vez. O painel também: as abas são links e os formulários enviam direto. O JS só adiciona conforto.

> [!question] Por que CSS puro e não Bootstrap ou Tailwind?
> O protótipo tinha identidade própria. Com tokens em CSS puro, o resultado é leve, sem build e fiel ao design, e o alto contraste é só outro conjunto de valores.

### 🪤 Perguntas "armadilha"

- **"Isso é um sistema de recomendação de verdade?"** Sim: é uma recomendação **baseada em conteúdo** (*content-based*), com perfil e itens no mesmo espaço vetorial. Não é *filtragem colaborativa*, que exigiria histórico de outros alunos.
- **"O que vocês fariam diferente?"** Validar os pesos com a coordenação antes, remover o código legado mais cedo e medir a aceitação real (quantos se matricularam no curso recomendado).
- **"O empate de 0,02 não é arbitrário?"** Foi calibrado: o `medir_empate` mostra que, com 0,02, cerca de 1 em cada 3 perfis sorteados fica em empate. Com tentativas reais, o mesmo comando mede de novo.

---

## 🧭 4. Limitações e próximos passos (slide final)

1. **Pesos** definidos pelo grupo, ainda sem validação empírica (a pergunta 6 da avaliação vai medir).
2. **Cursos generalistas** aparecem mais em 1º (Automação Industrial em 25,7% dos perfis simulados).
3. **Camada de IA** com o código pronto e testado; o experimento comparativo com a LLM real e a avaliação humana ainda por fazer.
4. **k-anonimato** construído e testado, mas desligado no painel por decisão do grupo.
5. Integração com o sistema de matrícula (SGSET): fora do escopo atual.

---

## ✅ 5. Checklist da véspera

- [ ] `python manage.py test` → **OK, 209 testes** (print no slide)
- [ ] Tabelas de fuso do MySQL carregadas (`python manage.py test core`)
- [ ] Banco com os 4 seeds + várias tentativas + 1 superusuário + 1 aluno + 1 link de avaliação respondido
- [ ] Testado o truque do empate (sempre a 1ª alternativa → aviso de confiança baixa)
- [ ] `LLM_ENABLED` com o valor certo para o que vai ser mostrado (na dúvida, `0`)
- [ ] Itens 3 a 7 da §1 corrigidos **ou** com resposta ensaiada
- [ ] Demo ensaiada do começo ao fim, **cronometrada**
- [ ] Vídeo ou prints de backup
- [ ] **Cada integrante sabe explicar a engine** e a parte que escreveu
- [ ] Conta à mão do cosseno pronta num slide
- [ ] Zoom do navegador e do editor em 125–150% (o projetor não perdoa)
- [ ] Abas abertas na ordem: `engine.py` → `models.py` → `web_views.py` → `metricas.py` → `privacidade.py` → `quiz.html` → `quiz.js`
