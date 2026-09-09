# AquaSuíno — acesso por perfil

Prefeitura: vê todas as propriedades, abre detalhes, consulta despesas consolidadas e cria contas de agricultores vinculadas a uma fazenda. Produtor: consulta e registra dados somente da propriedade vinculada à conta. O perfil Frivatti existente continua com seu painel agregado.

As permissões são verificadas no servidor para propriedades, leituras, fotos, dejetos, alertas, despesas e relatórios. Alterar a URL ou enviar outro `propriedade_id` não concede acesso. O perfil não é escolhido no login. O cadastro de agricultores sempre cria o perfil `produtor`.

## Executar localmente

1. Disponibilize um MongoDB local ou configure uma instância existente.
2. Crie um ambiente Python e instale `pip install -r backend/requirements-core.txt`. O arquivo original `requirements.txt` contém dependências adicionais da plataforma anterior; o arquivo core cobre esta API.
3. Copie `backend/.env.example` para `backend/.env.local`. Configure `MONGO_URL`, `DB_NAME` e um `JWT_SECRET` aleatório. Gere o segredo com `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Use `.env.local`, ignorado pelo Git: o repositório original já contém arquivos `.env` versionados. As variáveis do ambiente têm prioridade sobre ambos os arquivos.
4. Execute `python backend/create_admin.py` e informe os dados da primeira conta da prefeitura. Não há senha padrão, cadastro público de administradores nem alteração de contas existentes pelo comando.
5. Inicie a API: `python -m uvicorn server:app --app-dir backend --port 8000`.
6. Copie `frontend/.env.example` para `frontend/.env.local`, substituindo a URL de demonstração do `.env` original. Em `frontend`, execute `yarn install --frozen-lockfile` e `yarn start`.
7. Entre na conta da prefeitura e use **Cadastrar acesso de agricultor** para vincular cada pessoa à propriedade correta. A API de cadastro de propriedades (`POST /api/propriedades`) fica restrita à prefeitura.

O banco existente é preservado. As coleções `users`, `login_attempts` e `despesas` são usadas para os novos recursos. As despesas começam vazias e são armazenadas em centavos; os dados de retorno econômico e bônus continuam sendo estimativas, não gastos reais. Uma conta sem propriedade vinculada recebe uma mensagem orientando a procurar a prefeitura.

O script `backend/seed.py` contém dados fictícios e pode ser executado manualmente apenas em um banco de desenvolvimento. O endpoint público de seed foi removido. Não execute scripts de seed em um banco com dados reais.

## Publicação

Use HTTPS, `COOKIE_SECURE=true`, uma lista explícita de origens em `CORS_ORIGINS` e um segredo exclusivo do ambiente. Frontend e API devem ficar no mesmo site (preferencialmente `/api` por proxy reverso); cookies `SameSite=Lax` não suportam frontend e API em domínios sem relação entre si. O login usa cookie HttpOnly com validade de 12 horas e bloqueio de 15 minutos após cinco tentativas inválidas por e-mail.

Requisições de escrita exigem `X-Requested-With: AquaSuino`; o frontend já envia esse cabeçalho. Contas são consultadas no banco a cada requisição. Remover uma conta revoga seu acesso. Logout remove o cookie do navegador; tokens já copiados permanecem válidos até expirar, salvo exclusão da conta ou rotação do segredo.

O upload de fotos depende do serviço de armazenamento já existente e de `EMERGENT_LLM_KEY`. Login e despesas não dependem desse serviço.

## Contas, relatórios e atenção da prefeitura

- **Criar conta** no login permite o cadastro público de agricultor com uma nova fazenda. O perfil é fixado no servidor como `produtor`; não é possível informar o ID de outra fazenda nem criar uma conta da prefeitura. E-mails já cadastrados são rejeitados. O cadastro tem limite de cinco tentativas por endereço IP em 15 minutos. Para uma fazenda já existente, a prefeitura deve criar o acesso vinculado, evitando duplicidade. Não há verificação de e-mail nesta versão.

- **Contas** no menu da prefeitura lista usuários e permite ativar/desativar agricultores. A desativação e a troca/redefinição de senha revogam as sessões anteriores; reativar não restaura tokens antigos. Contas da prefeitura não podem ser desativadas por essa tela.
- **Minha conta** permite trocar a senha informando a atual. **Esqueci minha senha** solicita um e-mail de recuperação quando o SMTP está configurado. Como alternativa, a prefeitura confirma a identidade do agricultor e gera um link para entregar manualmente. Os links são de uso único, válidos por 30 minutos; o token é armazenado como hash, vai no fragmento do link e um novo link invalida o anterior.
- **Relatório individual** na fazenda gera PDF com datas opcionais, totais, meta, evolução mensal, leituras e despesas do período. O agricultor só pode gerar o relatório da própria fazenda. Consumo é contabilizado na data da leitura, sem rateio entre períodos.
- **Fazendas que precisam de atenção** calcula alertas a cada consulta: nenhuma leitura ou última leitura há mais de 35 dias; último consumo mais de 15% acima da média das até três leituras anteriores; gasto do mês mais de 50% acima da média dos meses com despesas nos três meses anteriores, exigindo ao menos dois meses com lançamentos. A referência usa a data UTC. Registros futuros de despesas não entram nesse cálculo. Os alertas desaparecem quando os dados deixam de atender às regras.
- **Excluir** na linha da despesa exige confirmação e atualiza o total. A exclusão é definitiva. O agricultor só pode excluir despesas da própria fazenda; a prefeitura pode excluir de qualquer fazenda. Relatórios e alertas consultados depois da exclusão usam os novos dados.

O HTML inicial não carrega mais os scripts de analytics e edição da plataforma anterior, para não expor links de recuperação a scripts externos.

## Recuperação por e-mail (Gmail/SMTP)

A tela **Esqueci minha senha** recebe o e-mail e solicita uma mensagem HTML, com alternativa em texto, botão de redefinição e prazo de 30 minutos. Contas inexistentes e desativadas recebem a mesma resposta pública, mas nenhum e-mail. O envio exige configuração real; sem SMTP, a interface informa indisponibilidade. Falhas do servidor de e-mail são registradas sem expor endereço, senha ou token. O envio ocorre em uma tarefa em segundo plano no processo da API; não há fila persistente ou retentativa automática. A aceitação pelo SMTP não garante entrega na caixa de entrada.

Para usar Gmail, ative a verificação em duas etapas e gere uma senha de app na conta Google. Veja https://support.google.com/mail/answer/185833?hl=pt-BR. Execute `python backend/configure_gmail.py` em um terminal local: ele solicita o remetente, a senha de app com entrada oculta e a URL do site, e grava apenas `backend/.env.local` (ignorado pelo Git). Reinicie a API. Não use a senha normal da conta Google.

Configuração manual equivalente: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_SECURITY=starttls`, `SMTP_FROM` e `SMTP_USERNAME` iguais ao remetente, `SMTP_PASSWORD` com a senha de app, e `PUBLIC_APP_URL` com a URL pública HTTPS. `localhost` funciona apenas no mesmo computador; para links abertos no celular ou por outros usuários, configure uma URL pública. O pedido tem limites por IP e por e-mail. A senha nunca é enviada por e-mail.

## Clareza e demonstração do protótipo

A página inicial explica público, problema, ações e próximo passo. `/demonstracao` contém uma experiência interativa com dados fictícios, isolada das APIs e do banco: leitura → despesa → resultado. Contas reais continuam exigindo login. Os painéis usam orientações de próximo passo, busca de fazendas e indicação explícita de estimativas. Uma leitura inválida, anterior à última ou abaixo do hidrômetro anterior é rejeitada; falhas ao anexar a foto são informadas sem ocultar que a leitura foi salva.

## Verificação

Instale `pip install pytest pytest-xdist httpx pypdf` e execute:

```text
python -m pytest -c backend/pytest.ini tests -q
```

Os testes exercitam a API por HTTP com banco em memória: login/logout, bloqueio de tentativas, consultas e gravações entre fazendas, fotos, relatórios, cadastro de contas, proteção de formulários externos e valores monetários. Para compilar a interface, execute `yarn build` em `frontend`. A validação com MongoDB e armazenamento reais exige configurar o ambiente acima.
