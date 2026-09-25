## Como instalar e rodar o projeto
**Atenção**: todos os comandos são executados na pasta raiz do projeto

Para criar a Virtual Env para o projeto
```bash
>>> uv init .

OU

>>> python3 -m venv .venv

```

Para instalar todas as dependências

```bash
>>> uv sync

OU

>>> .venv/Scripts/Activate
>>> pip install .
```

Após todas dependências terem sido instaladas, rode o projeto usando
```bash
>>> uv run fastapi dev

OU

>>> fastapi dev
```

A API irá iniciar em <a href='http://127.0.0.1:8000/'>127.0.0.1:8000/</a>
