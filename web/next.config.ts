import type { NextConfig } from "next";

const DEFAULT_API_ORIGIN = "http://127.0.0.1:8000";
const API_PROXY_TIMEOUT_MS = 180_000;

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
  rewrites: async () => [
    {
      source: "/api/:path*",
      destination: `${process.env.API_ORIGIN ?? DEFAULT_API_ORIGIN}/api/:path*`,
    },
  ],
};

export default nextConfig;
