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
      { source: "/public-profile/:path*", destination: "/learner/evidence", permanent: false },
      { source: "/settings/public-profile", destination: "/settings/consents", permanent: false },
      { source: "/home", destination: "/learner/learn", permanent: false },
      { source: "/learn", destination: "/learner/learn", permanent: false },
      { source: "/community", destination: "/company/dashboard", permanent: false },
      { source: "/applications", destination: "/company/learners", permanent: false },
      { source: "/skills", destination: "/learner/learn", permanent: false },
      { source: "/skills/:path*", destination: "/learner/learn", permanent: false },
      { source: "/goals/new", destination: "/learner/learn", permanent: false },
      { source: "/roadmaps/:path*", destination: "/learner/learn", permanent: false }
    ];
  }
};

export default config;
