import type { NextConfig } from "next";

// Order matters: the first import loads the repository-root .env into
// process.env, the second validates what it found. A missing or malformed value
// fails the build instead of a request in production.
import "./src/lib/load-root-env";
import "./src/lib/env";

const nextConfig: NextConfig = {/* config options here */};

export default nextConfig;
