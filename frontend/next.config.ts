import path from "node:path";
import type { NextConfig } from "next";

const repositoryRoot = path.join(process.cwd(), "..");

const nextConfig: NextConfig = {
  turbopack: { root: repositoryRoot },
  outputFileTracingRoot: repositoryRoot,
  outputFileTracingIncludes: {
    "/api/consult": [
      "../SKILL.md",
      "../references/**/*",
      "../scripts/**/*",
      "../assets/**/*",
    ],
  },
};

export default nextConfig;
