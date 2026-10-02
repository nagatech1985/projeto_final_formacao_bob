# DIO Explorer — MCP Server

Servidor MCP que expõe as capacidades do **DIO Explorer** como ferramentas acessíveis por Bob, Claude Desktop, ou qualquer cliente MCP compatível.

---

## Ferramentas disponíveis

| Ferramenta | Descrição |
|---|---|
| `buscar_trilhas` | Busca trilhas de aprendizado por tecnologia (Java, Python, React…) |
| `gerar_desafio` | Gera um desafio de código para uma tecnologia e nível de dificuldade |
| `gerar_certificado` | Emite um certificado de conclusão de trilha para um aluno |

---

## Pré-requisitos

- **Node.js ≥ 18**
- `npm install` + `npm run build` executados dentro desta pasta

---

## Build

```bash
cd "Dio Explorer/MCP"
npm install
npm run build
```

O arquivo de saída é `build/index.js`.

---

## Transportes

### 1. stdio (padrão — integração local com Bob)

Registrado automaticamente em `.bob/mcp.json`. Bob lança o processo e se comunica via stdin/stdout.

```bash
node build/index.js
```

### 2. HTTP / HTTPS / SSO (acesso remoto via API)

```bash
node build/index.js --http          # porta 3000
PORT=8080 node build/index.js --http   # porta customizada
```

Endpoints:

| Método | URL | Descrição |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/mcp` | MCP JSON-RPC (Streamable HTTP transport) |

Para expor com **HTTPS ou SSO**, coloque o servidor atrás de um reverse proxy (nginx, Caddy, IBM API Connect, AWS API Gateway) que termina TLS e encaminha as requisições para `localhost:<PORT>`.

---

## Autenticação via Bearer Token (opcional)

Defina a variável de ambiente `DIO_API_KEY` antes de iniciar o servidor:

```bash
DIO_API_KEY=seu-token-secreto node build/index.js --http
```

Clientes devem enviar o header:

```
Authorization: Bearer seu-token-secreto
```

Requisições sem o token recebem `HTTP 401`. Se `DIO_API_KEY` não estiver definida, o servidor aceita qualquer requisição (modo aberto).

---

## Registro em `.bob/mcp.json`

```json
{
  "mcpServers": {
    "dio-explorer": {
      "command": "node",
      "args": ["${workspaceFolder}/Dio Explorer/MCP/build/index.js"],
      "env": {
        "DIO_API_KEY": "${env:DIO_API_KEY}"
      }
    }
  }
}
```

---

## Estrutura de arquivos

```
Dio Explorer/MCP/
├── src/
│   └── index.ts        ← código-fonte principal
├── build/
│   └── index.js        ← saída compilada (gerada pelo build)
├── package.json
├── tsconfig.json
└── README.md
```
