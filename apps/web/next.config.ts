import type { NextConfig } from "next";

const config: NextConfig = {
  reactStrictMode: true,
  async redirects() {
    return [
      { source: "/messages", destination: "/company/reports", permanent: false },
      { source: "/portfolio", destination: "/learner/evidence", permanent: false },
      { source: "/portfolio/:path*", destination: "/learner/evidence", permanent: false },
      { source: "/career", destination: "/company/requirements", permanent: false },
      { source: "/opportunities", destination: "/company/requirements", permanent: false },
      { source: "/public-profile/:path*", destination: "/learner/evidence", permanent: false }
    ];
  }
};

export default config;
