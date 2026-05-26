"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppIcon, IconText } from "@/app/components/ui";
import { Section } from "@/app/components/ui/Section";
import uiStyles from "@/app/components/ui/ui.module.css";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { ComparisonTable4 } from "./ComparisonTable4";
import { EvidenceReportPreview } from "./EvidenceReportPreview";
import { FaqSection } from "./FaqSection";
import { HeroMock } from "./HeroMock";
import {
  LP_BRAND,
  LP_CHALLENGE_SECTION,
  LP_COMPARISON,
  LP_EVIDENCE_REPORT_SECTION,
  LP_FINAL_CTA,
  LP_HEADER_NAV,
  LP_HERO,
  LP_PRODUCT_DEMO,
  LP_ROLES,
  LP_SCENARIO,
  LP_TRUST_SECTION,
  LP_VALUE_FOOTNOTE,
  LP_VALUE_PROPS
} from "./lpContent";
import { PricingPackages } from "./PricingPackages";
import { ProductDemoTabs } from "./ProductDemoTabs";
import { ScenarioTimeline } from "./ScenarioTimeline";
import { StickyCtaBar } from "./StickyCtaBar";
import { TrustSection } from "./TrustSection";
import { WorkflowTimeline } from "./WorkflowTimeline";

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia === "undefined") {
      return;
    }
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return reduced;
}

function useRevealSections(reducedMotion: boolean) {
  useEffect(() => {
    const nodes = Array.from(document.querySelectorAll<HTMLElement>("[data-reveal='section']"));
    if (nodes.length === 0) {
      return;
    }
    if (reducedMotion || typeof IntersectionObserver === "undefined") {
      nodes.forEach((node) => node.classList.add(styles.revealVisible));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add(styles.revealVisible);
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    nodes.forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [reducedMotion]);
}

export function AIFieldReadyLanding() {
  const reducedMotion = usePrefersReducedMotion();
  useRevealSections(reducedMotion);

  return (
    <main className={`${uiStyles.marketingPage} ${styles.page}`}>
      <header className={`${uiStyles.lpHeader} ${styles.lpHeader}`}>
        <Link href="/" className={`${uiStyles.lpHeaderBrand} ${styles.headerBrand}`}>
          <span className={uiStyles.lpHeaderBrandMark} aria-hidden>
            ▲
          </span>
          <span className={styles.headerBrandText}>
            <strong>{LP_BRAND.name}</strong>
            <small>{LP_BRAND.tagline}</small>
          </span>
        </Link>

        <nav className={styles.headerNav} aria-label="セクションナビゲーション">
          {LP_HEADER_NAV.map((item) => (
            <Link key={item.href} href={item.href} className={styles.headerNavLink}>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className={`${uiStyles.lpHeaderActions} ${styles.headerActions}`}>
          <Link
            href="#sample-report"
            className={uiStyles.actionGhost}
            onClick={() => trackLpEvent("sample_report_cta_clicked", { source: "header" })}
          >
            <IconText icon="fileCheck2">サンプル証跡レポートを見る</IconText>
          </Link>
          <Link
            href="#demo"
            className={uiStyles.actionPrimary}
            onClick={() => trackLpEvent("hero_demo_cta_clicked", { source: "header" })}
          >
            <IconText icon="rocket">無料デモを見る</IconText>
          </Link>
          <Link href="/auth/sign-in" className={styles.loginLink}>
            ログイン
          </Link>
        </div>
      </header>

      <section className={`${uiStyles.hero} ${uiStyles.heroMarketing} ${styles.hero}`} data-reveal="section">
        <div className={styles.heroContent}>
          <span className={`${uiStyles.heroEyebrow} ${uiStyles.heroEyebrowMarketing}`}>
            SES企業向け B2B 育成プラットフォーム
          </span>
          <h1 className={`${uiStyles.heroTitle} ${styles.heroTitle}`}>{LP_HERO.heading}</h1>
          <p className={styles.heroBrandLine} aria-label="サービス名">
            <span className={styles.heroBrandMark} aria-hidden>
              ▲
            </span>
            <span>
              <strong>{LP_BRAND.name}</strong>
              <small>{LP_BRAND.tagline}</small>
            </span>
          </p>
          <p className={uiStyles.heroLead}>{LP_HERO.subcopy}</p>

          <ul className={styles.heroOutcomeList} aria-label="導入で得られる成果">
            {LP_HERO.outcomes.map((outcome) => (
              <li key={outcome.title} className={styles.heroOutcomeCard}>
                <strong>{outcome.title}</strong>
                <p>{outcome.body}</p>
              </li>
            ))}
          </ul>

          <div className={styles.heroActions}>
            <Link
              href="/business/sign-up"
              className={uiStyles.actionPrimary}
              onClick={() => trackLpEvent("diagnosis_cta_clicked", { source: "hero" })}
            >
              <IconText icon="rocket">待機人材10名の育成診断を相談する</IconText>
            </Link>
            <Link
              href="#sample-report"
              className={uiStyles.actionGhost}
              onClick={() => trackLpEvent("sample_report_cta_clicked", { source: "hero" })}
            >
              <IconText icon="notebookText">サンプル証跡レポートを見る</IconText>
            </Link>
            <Link
              href="#demo"
              className={uiStyles.actionGhost}
              onClick={() => trackLpEvent("hero_demo_cta_clicked", { source: "hero" })}
            >
              <IconText icon="layoutDashboard">無料デモを見る</IconText>
            </Link>
          </div>
          <p className={styles.heroMessage}>
            営業・教育・経営の共通言語は「実務証跡」。提案判断を早める材料を、SaaSで標準出力します。
          </p>
        </div>
        <HeroMock reducedMotion={reducedMotion} />
      </section>

      <div id="challenges" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title={LP_CHALLENGE_SECTION.title} meta={LP_CHALLENGE_SECTION.meta}>
          <div className={styles.challengeGrid}>
            {LP_CHALLENGE_SECTION.items.map((challenge, index) => (
              <article key={challenge.title} className={styles.challengeCard}>
                <span className={styles.challengeIndex}>0{index + 1}</span>
                <h3>{challenge.title}</h3>
                <p>{challenge.body}</p>
              </article>
            ))}
          </div>
        </Section>
      </div>

      <div id="solution" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section
          title="AI Field Readyとは"
          meta="経営者 / 営業 / 教育担当の 3 つの立場から、導入価値を整理します。"
        >
          <div className={styles.valueGrid}>
            {LP_VALUE_PROPS.map((prop) => (
              <article key={prop.id} className={styles.valueCard}>
                <span className={styles.valueIconBadge}>
                  <AppIcon name={prop.icon} size={16} />
                </span>
                <p className={styles.valueStakeholder}>{prop.stakeholder}</p>
                <h3>{prop.benefit}</h3>
                <p>{prop.detail}</p>
              </article>
            ))}
          </div>
          <p className={styles.valueFootnote}>{LP_VALUE_FOOTNOTE}</p>
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section title={LP_TRUST_SECTION.title} meta={LP_TRUST_SECTION.meta}>
          <TrustSection />
        </Section>
      </div>

      <div id="demo" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title={LP_PRODUCT_DEMO.title} meta={LP_PRODUCT_DEMO.meta}>
          <ProductDemoTabs reducedMotion={reducedMotion} />
        </Section>
      </div>

      <div id="evidence-report" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone4}`}>
        <Section
          title={
            <>
              <span className={styles.sectionHeadlineEyebrow}>{LP_EVIDENCE_REPORT_SECTION.eyebrow}</span>
              <span className={styles.sectionHeadline}>{LP_EVIDENCE_REPORT_SECTION.title}</span>
            </>
          }
          meta={LP_EVIDENCE_REPORT_SECTION.meta}
        >
          <div id="sample-report">
            <EvidenceReportPreview />
          </div>
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section
          title="育成できるAI/DX補助ロール"
          meta="案件現場で説明しやすい、実務タスク単位のロールを 6 種育成対象としています。"
        >
          <div className={styles.roleGrid}>
            {LP_ROLES.map((role) => (
              <div key={role} className={styles.roleCard}>
                <AppIcon name="target" size={16} />
                <span>{role}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section
          title="業務フロー"
          meta="案件要件 → 必要スキル → 育成 → 提出 → レビュー → 実務証跡 → 提案サマリーの一気通貫プロセス。"
        >
          <WorkflowTimeline reducedMotion={reducedMotion} />
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section title={LP_COMPARISON.title} meta={LP_COMPARISON.meta}>
          <ComparisonTable4 />
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section title={LP_SCENARIO.title} meta={LP_SCENARIO.meta}>
          <ScenarioTimeline />
        </Section>
      </div>

      <div id="pricing" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone4}`}>
        <Section
          title="料金プラン（導入パッケージ）"
          meta="導入目的別に 3 つのパッケージを用意しています。価格は補足情報、まずは得られる価値で選んでください。"
        >
          <PricingPackages />
        </Section>
      </div>

      <div id="faq" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title="FAQ" meta="導入検討時によくいただく質問。重要な 5 問は初期から開いてあります。">
          <FaqSection />
        </Section>
      </div>

      <section id="final-cta" className={styles.finalCta} data-reveal="section">
        <p className={styles.finalCtaLabel}>{LP_FINAL_CTA.eyebrow}</p>
        <h2>{LP_FINAL_CTA.title}</h2>
        <p>{LP_FINAL_CTA.body}</p>
        <div className={styles.finalCtaActions}>
          <Link
            href="/business/sign-up"
            className={uiStyles.actionPrimary}
            onClick={() => {
              trackLpEvent("diagnosis_cta_clicked", { source: "final_cta" });
              trackLpEvent("final_cta_clicked", { cta: "diagnosis" });
            }}
          >
            <IconText icon="rocket">{LP_FINAL_CTA.primaryCta}</IconText>
          </Link>
          <Link
            href="#sample-report"
            className={uiStyles.actionGhost}
            onClick={() => {
              trackLpEvent("sample_report_cta_clicked", { source: "final_cta" });
              trackLpEvent("final_cta_clicked", { cta: "sample_report" });
            }}
          >
            {LP_FINAL_CTA.secondaryCta}
          </Link>
        </div>
        <p className={styles.finalCtaNote}>
          ※ 診断レポートは無料です。導入の判断は診断後に決めていただけます。
        </p>
      </section>

      <StickyCtaBar />
    </main>
  );
}
