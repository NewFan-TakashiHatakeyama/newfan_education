import type { Metadata } from "next";

import { AIFieldReadyLanding } from "@/app/components/marketing/AIFieldReadyLanding";
import { StructuredData } from "@/app/components/marketing/StructuredData";

export const metadata: Metadata = {
  title: "待機人材を、AI/DX案件で提案できる状態へ。｜AI Field Ready",
  description:
    "AI Field Ready は、SES企業の若手・待機人材に対して、案件要件から逆算した育成ロードマップ、実務演習、AIレビュー、メンター承認を提供し、営業提案・面談・配属判断に使える「実務証跡レポート」を作るB2B育成プラットフォームです。",
  openGraph: {
    title: "待機人材を、AI/DX案件で提案できる状態へ。｜AI Field Ready",
    description:
      "案件要件から逆算した育成ロードマップ・AIレビュー・実務証跡レポートで、SES企業の待機人材を商談化につなげる B2B 育成プラットフォーム。",
    type: "website",
    locale: "ja_JP",
    siteName: "AI Field Ready"
  },
  twitter: {
    card: "summary_large_image",
    title: "待機人材を、AI/DX案件で提案できる状態へ。｜AI Field Ready",
    description:
      "案件要件から逆算した育成ロードマップと実務証跡レポートで、SES企業の待機人材を商談化までつなぐ B2B 育成プラットフォーム。"
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
