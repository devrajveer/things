/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@yourplatform/shared"],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  }
};

export default nextConfig;
