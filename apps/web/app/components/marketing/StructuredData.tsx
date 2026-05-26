import { LP_BRAND, LP_FAQS, LP_HERO } from "./lpContent";

/**
 * JSON-LD 構造化データ。
 *
 * - サーバーコンポーネントとして描画し、検索エンジンが LP のクロール時に
 *   FAQPage / SoftwareApplication をパースできるようにする。
 * - クライアントの `AIFieldReadyLanding` は `"use client"` 指定のため、
 *   `<script type="application/ld+json">` をここに分離してサーバー描画する。
 */
export function StructuredData() {
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: LP_FAQS.map((faq) => ({
      "@type": "Question",
      name: faq.q,
      acceptedAnswer: {
        "@type": "Answer",
        text: faq.a
      }
    }))
  };

  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: LP_BRAND.name,
    applicationCategory: "BusinessApplication",
    applicationSubCategory: "HR / Training Platform",
    operatingSystem: "Web",
    description: LP_HERO.subcopy,
    offers: {
      "@type": "Offer",
      price: "200000",
      priceCurrency: "JPY"
    }
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareSchema) }}
      />
    </>
  );
}
