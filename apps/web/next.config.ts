import type { NextConfig } from "next";

const skipTypecheck = process.env.SKIP_NEXT_TYPECHECK === "true";

const nextConfig: NextConfig = {
  output: "standalone",
  eslint: {
    ignoreDuringBuilds: skipTypecheck,
  },
  typescript: {
    ignoreBuildErrors: skipTypecheck,
  },
};

export default nextConfig;
