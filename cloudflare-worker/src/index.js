/**
 * A2A Data Matrix Quad-Oracle — Cloudflare Global Edge Cache & Stateless MCP/x402 Gateway
 * Caches discovery & command center pages at edge for 60s and proxies paid x402 / MCP requests cleanly.
 */

const EDGE_CACHEABLE_PATHS = new Set([
  "/",
  "/llms.txt",
  "/.well-known/mcp.json",
  "/.well-known/x402-manifest.json",
]);

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const originUrl = new URL(url.pathname + url.search, env.ORIGIN_BASE_URL);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, X-Payment, X-Prepaid-Bearer, X-Idempotency-Key, X-Admin-Token",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    if (request.method === "GET" && EDGE_CACHEABLE_PATHS.has(url.pathname)) {
      const cache = caches.default;
      let response = await cache.match(request);
      if (!response) {
        const originResp = await fetch(originUrl.toString(), {
          headers: { "User-Agent": "A2A-Matrix-Quad-Edge/2.0" },
        });
        response = new Response(originResp.body, originResp);
        response.headers.set("Cache-Control", "public, s-maxage=60, max-age=30");
        response.headers.set("X-Edge-Cache", "MISS");
        ctx.waitUntil(cache.put(request, response.clone()));
      } else {
        response = new Response(response.body, response);
        response.headers.set("X-Edge-Cache", "HIT");
      }
      return response;
    }

    const proxyReq = new Request(originUrl.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
    });
    const originResponse = await fetch(proxyReq);
    const out = new Response(originResponse.body, originResponse);
    out.headers.set("Mcp-Stateless-Mode", "enabled");
    return out;
  },
};
