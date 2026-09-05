# Sistema de Atendimento de Pronto Socorro

MVP web para acompanhar o atendimento desde a recepcao ate a alta medica. O front-end usa HTML e CSS renderizados pelo servidor; o back-end usa Python com Flask; os dados ficam em SQLite.

## Funcionalidades iniciais

- Recepcao: cadastro do paciente, abertura, consulta, alteracao e cancelamento do atendimento.
- Triagem: registro de sinais vitais, queixas e classificacao pelo protocolo de Manchester.
- Medico: painel ordenado por prioridade, registro de medicacoes e finalizacao do atendimento.
- Regras de fluxo: atendimentos cancelados ou finalizados ficam bloqueados para alteracoes.

## Como executar

Requer Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Acesse `http://127.0.0.1:5000`. O banco `pronto_socorro.db` e criado automaticamente na primeira execucao.

## Testes

```powershell
python -m unittest discover -s tests -v
```

## Estrutura

```text
app/
  static/css/       estilos do front-end
  templates/        paginas HTML
  __init__.py       fabrica da aplicacao
  db.py             acesso e inicializacao do banco
  routes.py         regras e rotas do sistema
  schema.sql        modelo relacional
tests/              testes do fluxo principal
run.py              ponto de entrada local
```

## Proximos passos recomendados

1. Validar os campos obrigatorios do paciente com a equipe e o professor.
2. Confirmar as regras clinicas usadas para definir a classificacao Manchester; nesta versao, a classificacao e selecionada pelo profissional.
3. Adicionar autenticacao e perfis de recepcao, enfermagem e medico.
4. Migrar para PostgreSQL se o sistema passar a ser usado por varios computadores.
5. Definir politica de privacidade, auditoria e controle de acesso antes de usar dados reais.
