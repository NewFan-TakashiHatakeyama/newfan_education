import type { Metadata } from "next";

import { AIFieldReadyLanding } from "@/app/components/marketing/AIFieldReadyLanding";
import { StructuredData } from "@/app/components/marketing/StructuredData";
import { LP_SEO } from "@/app/components/marketing/lpContent";

export const metadata: Metadata = {
  title: LP_SEO.title,
  description: LP_SEO.description,
  openGraph: {
    title: LP_SEO.title,
    description: LP_SEO.description,
    type: "website",
    locale: "ja_JP",
    siteName: "AI Field Ready Enterprise"
  },
  twitter: {
    card: "summary_large_image",
    title: LP_SEO.title,
    description: LP_SEO.description
  }
};

export default function LandingPage() {
  return (
    <>
      <StructuredData />
      <AIFieldReadyLanding />
    </>
  );
}
