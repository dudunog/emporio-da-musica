import type { NextConfig } from "next";

const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";
const API_PROXY_TIMEOUT_MS = 180_000;
const CHAT_ENDPOINT = "/api/chat";

const nextConfig: NextConfig = {
  agentRules: false,
  devIndicators: false,
  experimental: { proxyTimeout: API_PROXY_TIMEOUT_MS },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  redirects: async () => [{ source: "/_global-error", destination: "/", permanent: false }],
  rewrites: async () => [{ source: CHAT_ENDPOINT, destination: `${process.env.API_ORIGIN ?? DEFAULT_API_ORIGIN}${CHAT_ENDPOINT}` }],
};

export default nextConfig;
