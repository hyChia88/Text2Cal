import type { NextConfig } from "next";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // This will completely bypass ESLint during builds
    ignoreDuringBuilds: true,
  },
  // Add this if you're also getting TypeScript errors
  typescript: {
    // This will ignore TypeScript errors during builds
    ignoreBuildErrors: true,
  }
}

module.exports = nextConfig
