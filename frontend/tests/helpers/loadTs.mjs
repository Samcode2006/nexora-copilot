import path from "node:path";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const FRONTEND_ROOT = path.resolve(__dirname, "../..");

/**
 * Load a TypeScript/TSX source module using Vite's built-in transform pipeline
 * so tests exercise real `src/` files without extra test-runner dependencies.
 */
export async function withViteSsr(fn) {
  const server = await createServer({
    root: FRONTEND_ROOT,
    logLevel: "silent",
    server: { middlewareMode: true, watch: null },
    appType: "custom",
    optimizeDeps: { noDiscovery: true },
  });
  try {
    return await fn((specifier) => server.ssrLoadModule(specifier));
  } finally {
    await server.close();
  }
}

