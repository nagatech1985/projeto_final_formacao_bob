#!/usr/bin/env node
/**
 * DIO Explorer — MCP Server
 *
 * Expõe as três capacidades do DIO Explorer como ferramentas MCP:
 *   • buscar_trilhas    — busca trilhas de estudo por tecnologia
 *   • gerar_desafio     — gera um desafio de código para uma tecnologia e nível
 *   • gerar_certificado — emite um certificado de conclusão de trilha
 *
 * Transportes suportados:
 *   • stdio  (padrão — integração local com Bob/Claude Desktop)
 *   • HTTP   (flag --http  — acesso remoto via API/HTTPS/SSO)
 *
 * Autenticação HTTP (opcional):
 *   Defina a variável de ambiente DIO_API_KEY para habilitar Bearer-token.
 *   Requisições sem o header correto recebem HTTP 401.
 *   Se DIO_API_KEY não estiver definida, o servidor aceita qualquer requisição.
 *
 * Uso:
 *   node build/index.js               # stdio (Bob local)
 *   node build/index.js --http        # HTTP na porta 3000 (ou $PORT)
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import * as fs from "node:fs";
import * as path from "node:path";
import * as http from "node:http";
import * as crypto from "node:crypto";
import { fileURLToPath } from "node:url";

// ─── Paths ────────────────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// build/index.js  →  MCP/  →  Dio Explorer/  →  Data/trilhas_dio.json
const DATA_FILE = path.resolve(
  __dirname,
  "..",
  "..",
  "Data",
  "trilhas_dio.json"
);

// ─── Types ────────────────────────────────────────────────────────────────────

interface Promocao {
  desconto_percentual: number;
  validade: string | null;
  codigo_cupom: string | null;
}

interface Live {
  titulo: string;
  data: string;
  instrutor: string;
}

interface Trilha {
  id: number;
  nome: string;
  tecnologia: string;
  nivel: string;
  numero_modulos: number;
  xp_total: number;
  badges_disponiveis: string[];
  promocoes: Promocao;
  vitalicio: boolean;
  lives_ao_vivo: Live[];
}

// ─── Data loader ─────────────────────────────────────────────────────────────

function carregarTrilhas(): Trilha[] {
  const raw = fs.readFileSync(DATA_FILE, "utf-8");
  return (JSON.parse(raw) as { trilhas: Trilha[] }).trilhas;
}

// ─── Business logic (mirror of dio_explorer.py) ───────────────────────────────

function buscarTrilhas(tecnologia: string, trilhas: Trilha[]): Trilha[] {
  const termo = tecnologia.trim().toLowerCase();
  return trilhas.filter((t) => t.tecnologia.toLowerCase().includes(termo));
}

function formatarPlanoDeEstudos(trilha: Trilha): string {
  const promo = trilha.promocoes;
  const vitalicio = trilha.vitalicio ? "Sim" : "Não";

  const lines: string[] = [
    `# 📚 Plano de Estudos — ${trilha.nome}`,
    "",
    `**🏷️ Tecnologia:** ${trilha.tecnologia}  `,
    `**📊 Nível:** ${trilha.nivel}  `,
    `**📦 Total de Módulos:** ${trilha.numero_modulos}  `,
    `**⭐ XP Total ao concluir:** ${trilha.xp_total} XP  `,
    `**♾️ Acesso Vitalício:** ${vitalicio}  `,
    "",
    "---",
    "",
    "## 🏅 Badges Disponíveis",
    "",
    ...trilha.badges_disponiveis.map((b) => `- [ ] ${b}`),
    "",
    "---",
    "",
    "## 🎥 Lives ao Vivo",
    "",
    ...(trilha.lives_ao_vivo.length > 0
      ? trilha.lives_ao_vivo.map(
          (l) => `- **${l.titulo}** — 📅 ${l.data} — 👨‍🏫 ${l.instrutor}`
        )
      : ["Nenhuma live agendada."]),
    "",
    "---",
    "",
    "## 🏷️ Promoção Ativa",
    "",
    promo.desconto_percentual > 0
      ? `> 🔖 Use o cupom **${promo.codigo_cupom}** e ganhe **${promo.desconto_percentual}% de desconto**! Válido até ${promo.validade}.`
      : "> Nenhuma promoção ativa no momento.",
    "",
    "---",
  ];

  return lines.join("\n");
}

const NIVEIS_VALIDOS = new Set([
  "basico",
  "básico",
  "intermediario",
  "intermediário",
  "avancado",
  "avançado",
]);
const NIVEL_PADRAO = "Intermediário";

const XP_POR_NIVEL: Record<string, number> = {
  basico: 200,
  básico: 200,
  intermediario: 800,
  intermediário: 800,
  avancado: 1800,
  avançado: 1800,
};

const TIPOS_POR_NIVEL: Record<string, string[]> = {
  basico: ["Algoritmo", "Manipulação de Strings", "Estrutura de Laço"],
  básico: ["Algoritmo", "Manipulação de Strings", "Estrutura de Laço"],
  intermediario: ["Estrutura de Dados", "Orientação a Objetos", "Consumo de API"],
  intermediário: ["Estrutura de Dados", "Orientação a Objetos", "Consumo de API"],
  avancado: ["Design Pattern", "Concorrência/Async", "Algoritmo de Grafos"],
  avançado: ["Design Pattern", "Concorrência/Async", "Algoritmo de Grafos"],
};

function normalizarNivel(nivel: string): { nivelNorm: string; usadoPadrao: boolean } {
  const lower = nivel.trim().toLowerCase();
  if (NIVEIS_VALIDOS.has(lower)) {
    return { nivelNorm: nivel.trim(), usadoPadrao: false };
  }
  return { nivelNorm: NIVEL_PADRAO, usadoPadrao: true };
}

function gerarDesafio(tecnologia: string, nivel: string) {
  const { nivelNorm, usadoPadrao } = normalizarNivel(nivel);
  const nivelKey = nivelNorm.toLowerCase();
  const tipos = TIPOS_POR_NIVEL[nivelKey] ?? TIPOS_POR_NIVEL["intermediário"];
  const tipo = tipos[Math.floor(Math.random() * tipos.length)];
  const xp = XP_POR_NIVEL[nivelKey] ?? 800;
  return { tecnologia: tecnologia.trim(), nivel: nivelNorm, tipo, xp, aviso_padrao: usadoPadrao };
}

function buscarTrilhaParaCertificado(
  nomeTrilha: string,
  trilhas: Trilha[]
): Trilha | null {
  const termo = nomeTrilha.trim().toLowerCase();
  return (
    trilhas.find((t) => t.nome.toLowerCase().includes(termo)) ??
    trilhas.find((t) => t.tecnologia.toLowerCase().includes(termo)) ??
    null
  );
}

function gerarCodigoVerificacao(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let code = "DIO-";
  for (let i = 0; i < 12; i++) {
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

function gerarCertificado(nomeAluno: string, trilha: Trilha) {
  const hoje = new Date();
  const emitidoEm = `${String(hoje.getDate()).padStart(2, "0")}/${String(
    hoje.getMonth() + 1
  ).padStart(2, "0")}/${hoje.getFullYear()}`;
  return {
    nome_aluno: nomeAluno.trim(),
    trilha: trilha.nome,
    tecnologia: trilha.tecnologia,
    nivel: trilha.nivel,
    numero_modulos: trilha.numero_modulos,
    xp_total: trilha.xp_total,
    vitalicio: trilha.vitalicio,
    badges: trilha.badges_disponiveis,
    codigo_verificacao: gerarCodigoVerificacao(),
    emitido_em: emitidoEm,
  };
}

// ─── MCP Server ───────────────────────────────────────────────────────────────

const server = new McpServer({
  name: "dio-explorer",
  version: "1.0.0",
});

// Tool 1 — buscar_trilhas
server.registerTool(
  "buscar_trilhas",
  {
    description:
      "Busca trilhas de aprendizado na plataforma DIO pela tecnologia desejada. " +
      "Retorna um plano de estudos formatado com módulos, badges, lives e promoções.",
    inputSchema: {
      tecnologia: z
        .string()
        .min(1)
        .describe(
          "Nome da tecnologia a buscar (ex: Java, Python, React). Aceita termos parciais."
        ),
    },
  },
  async ({ tecnologia }) => {
    try {
      const trilhas = carregarTrilhas();
      const encontradas = buscarTrilhas(tecnologia, trilhas);
      if (encontradas.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: `Nenhuma trilha encontrada para a tecnologia: **${tecnologia}**.\n\nTente outro termo como Java, Python, React, Angular, TypeScript, etc.`,
            },
          ],
        };
      }
      const planos = encontradas.map(formatarPlanoDeEstudos).join("\n\n---\n\n");
      return { content: [{ type: "text", text: planos }] };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: `Erro ao buscar trilhas: ${err instanceof Error ? err.message : String(err)}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// Tool 2 — gerar_desafio
server.registerTool(
  "gerar_desafio",
  {
    description:
      "Gera um desafio de código para uma tecnologia e nível de dificuldade. " +
      "Níveis válidos: básico, intermediário, avançado (aceita variações sem acento).",
    inputSchema: {
      tecnologia: z
        .string()
        .min(1)
        .describe("Tecnologia do desafio (ex: Python, Java, TypeScript)."),
      nivel: z
        .string()
        .default("intermediário")
        .describe(
          "Nível de dificuldade: básico | intermediário | avançado. Padrão: intermediário."
        ),
    },
  },
  async ({ tecnologia, nivel }) => {
    try {
      const desafio = gerarDesafio(tecnologia, nivel);
      const aviso = desafio.aviso_padrao
        ? `\n> ⚠️ Nível não reconhecido. Usando **${NIVEL_PADRAO}** como padrão.\n`
        : "";
      const texto =
        `${aviso}` +
        `# ⚡ Desafio DIO — ${desafio.tecnologia} · Nível ${desafio.nivel}\n\n` +
        `**🎯 Tipo:** ${desafio.tipo}  \n` +
        `**⭐ XP ao concluir:** ${desafio.xp} XP  \n`;
      return { content: [{ type: "text", text: texto }] };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: `Erro ao gerar desafio: ${err instanceof Error ? err.message : String(err)}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// Tool 3 — gerar_certificado
server.registerTool(
  "gerar_certificado",
  {
    description:
      "Emite um certificado de conclusão de trilha DIO para um aluno. " +
      "Busca a trilha pelo nome ou tecnologia (parcial, case-insensitive).",
    inputSchema: {
      nome_aluno: z.string().min(1).describe("Nome completo do aluno."),
      nome_trilha: z
        .string()
        .min(1)
        .describe(
          "Nome ou tecnologia da trilha concluída (ex: 'Fullstack Java + Angular', 'Python')."
        ),
    },
  },
  async ({ nome_aluno, nome_trilha }) => {
    try {
      const trilhas = carregarTrilhas();
      const trilha = buscarTrilhaParaCertificado(nome_trilha, trilhas);
      if (!trilha) {
        return {
          content: [
            {
              type: "text",
              text: `Trilha não encontrada: **${nome_trilha}**.\n\nVerifique o nome ou tecnologia e tente novamente.`,
            },
          ],
        };
      }
      const cert = gerarCertificado(nome_aluno, trilha);
      const vitalicioStr = cert.vitalicio ? "Sim ♾️" : "Não ❌";
      const badgesLines = cert.badges.map((b: string) => `- ✅ ${b}`).join("\n");
      const texto =
        "# 🏆 Certificado de Conclusão\n\n" +
        "**Certificamos que**\n\n" +
        `## ${cert.nome_aluno}\n\n` +
        "concluiu com êxito a trilha de aprendizado:\n\n" +
        "---\n\n" +
        `## 🎯 ${cert.trilha}\n\n` +
        `| Campo | Detalhes |\n` +
        `|---|---|\n` +
        `| **Tecnologia** | ${cert.tecnologia} |\n` +
        `| **Nível** | ${cert.nivel} |\n` +
        `| **Módulos Concluídos** | ${cert.numero_modulos} de ${cert.numero_modulos} ✅ |\n` +
        `| **XP Conquistado** | ${cert.xp_total} XP ⭐ |\n` +
        `| **Acesso Vitalício** | ${vitalicioStr} |\n\n` +
        "---\n\n" +
        "## 🏅 Badges Conquistadas\n\n" +
        `${badgesLines}\n\n` +
        "---\n\n" +
        "## 📜 Informações do Certificado\n\n" +
        `| Campo | Valor |\n` +
        `|---|---|\n` +
        `| **Emitido em** | ${cert.emitido_em} |\n` +
        `| **Código de Verificação** | ${cert.codigo_verificacao} |\n` +
        `| **Plataforma** | Digital Innovation One |\n` +
        `| **Validade** | Vitalício |\n`;
      return { content: [{ type: "text", text: texto }] };
    } catch (err) {
      return {
        content: [
          {
            type: "text",
            text: `Erro ao gerar certificado: ${err instanceof Error ? err.message : String(err)}`,
          },
        ],
        isError: true,
      };
    }
  }
);

// ─── Transport selection ──────────────────────────────────────────────────────

const useHttp = process.argv.includes("--http");

if (useHttp) {
  // ── HTTP transport ───────────────────────────────────────────────────────
  const PORT = parseInt(process.env["PORT"] ?? "3000", 10);
  const API_KEY = process.env["DIO_API_KEY"]; // optional Bearer token

  /**
   * Minimal Streamable-HTTP-compatible MCP endpoint.
   *
   * POST /mcp  — MCP JSON-RPC messages
   * GET  /health — liveness check
   *
   * To expose over HTTPS/SSO: place this server behind a reverse proxy
   * (nginx, Caddy, API Gateway, IBM API Connect) that terminates TLS
   * and adds the required auth headers.
   */
  const { StreamableHTTPServerTransport } = await import(
    "@modelcontextprotocol/sdk/server/streamableHttp.js"
  );

  const httpServer = http.createServer(async (req, res) => {
    // CORS — allow any origin for open API access
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

    if (req.method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    // Health check
    if (req.method === "GET" && req.url === "/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok", server: "dio-explorer", version: "1.0.0" }));
      return;
    }

    // Bearer-token auth (only when DIO_API_KEY is set)
    if (API_KEY) {
      const authHeader = req.headers["authorization"] ?? "";
      const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : "";
      const keyBuf = Buffer.from(API_KEY);
      const tokBuf = Buffer.alloc(keyBuf.length);
      Buffer.from(token).copy(tokBuf);
      if (!crypto.timingSafeEqual(tokBuf, keyBuf)) {
        res.writeHead(401, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Unauthorized — invalid or missing API key." }));
        return;
      }
    }

    // Hand off to the SDK streamable HTTP transport
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    await server.connect(transport);
    await transport.handleRequest(req, res);
  });

  httpServer.listen(PORT, () => {
    console.error(`[dio-explorer] HTTP MCP server listening on port ${PORT}`);
    if (API_KEY) {
      console.error(`[dio-explorer] Bearer-token auth ENABLED (DIO_API_KEY is set)`);
    } else {
      console.error(`[dio-explorer] Bearer-token auth DISABLED (set DIO_API_KEY to enable)`);
    }
    console.error(`[dio-explorer] Health:       GET  http://localhost:${PORT}/health`);
    console.error(`[dio-explorer] MCP endpoint: POST http://localhost:${PORT}/mcp`);
  });
} else {
  // ── stdio transport (default — local Bob integration) ────────────────────
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[dio-explorer] MCP server running on stdio");
}
