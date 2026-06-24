"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppIcon, IconText } from "@/app/components/ui";
import { Section } from "@/app/components/ui/Section";
import uiStyles from "@/app/components/ui/ui.module.css";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { ComparisonTable4 } from "./ComparisonTable4";
import { CurriculumTimeline } from "./CurriculumTimeline";
import { DeliverablesPreview } from "./DeliverablesPreview";
import { FaqSection } from "./FaqSection";
import { HeroMock } from "./HeroMock";
import { ImplementationFlowSection } from "./ImplementationFlowSection";
import {
  LP_BRAND,
  LP_CHALLENGE_SECTION,
  LP_CTA,
  LP_FINAL_CTA,
  LP_HEADER_NAV,
  LP_HERO,
  LP_PRODUCT_DEMO,
  LP_SOLUTION_SECTION,
  LP_USE_CASES
} from "./lpContent";
import { PricingPackages } from "./PricingPackages";
import { ProductDemoTabs } from "./ProductDemoTabs";
import { ReviewSystemSection } from "./ReviewSystemSection";
import { RoleTracksSection } from "./RoleTracksSection";
import { StakeholderValueTabs } from "./StakeholderValueTabs";
import { StickyCtaBar } from "./StickyCtaBar";
import { UseCasesSection } from "./UseCasesSection";

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia === "undefined") return;
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
    if (nodes.length === 0) return;
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

  const heroLines = LP_HERO.heading.split("\n");

  return (
    <main className={`${uiStyles.marketingPage} ${styles.page}`}>
      <header className={`${uiStyles.lpHeader} ${styles.lpHeader}`}>
        <Link href="/" className={`${uiStyles.lpHeaderBrand} ${styles.headerBrand}`}>
          <span className={uiStyles.lpHeaderBrandMark} aria-hidden>▲</span>
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
            href="#curriculum-download"
            className={uiStyles.actionGhost}
            onClick={() => trackLpEvent("curriculum_download_clicked", { source: "header" })}
          >
            <IconText icon="notebookText">{LP_CTA.secondary}</IconText>
          </Link>
          <Link
            href="/business/sign-up"
            className={uiStyles.actionPrimary}
            onClick={() => trackLpEvent("hero_primary_cta_clicked", { source: "header" })}
          >
            <IconText icon="rocket">{LP_CTA.primary}</IconText>
          </Link>
          <Link href="/auth/sign-in" className={styles.loginLink}>ログイン</Link>
        </div>
      </header>

      <section className={`${uiStyles.hero} ${uiStyles.heroMarketing} ${styles.hero} ${styles.heroSplit}`} data-reveal="section">
        <div className={styles.heroContent}>
          <span className={`${uiStyles.heroEyebrow} ${uiStyles.heroEyebrowMarketing}`}>{LP_HERO.badge}</span>
          <h1 className={`${uiStyles.heroTitle} ${styles.heroTitle}`}>
            {heroLines.map((line, i) => (
              <span key={line}>
                {line}
                {i < heroLines.length - 1 ? <br /> : null}
              </span>
            ))}
          </h1>
          <p className={styles.heroLead}>{LP_HERO.subcopy}</p>
          <p className={styles.heroMessage}>{LP_HERO.trustMicrocopy}</p>

          <div className={styles.heroBeforeAfter}>
            <div>
              <span>Before</span>
              <p>{LP_HERO.beforeAfter.before}</p>
            </div>
            <div>
              <span>After</span>
              <p>{LP_HERO.beforeAfter.after}</p>
            </div>
          </div>

          <div className={styles.heroActions}>
            <Link
              href="/business/sign-up"
              className={uiStyles.actionPrimary}
              onClick={() => trackLpEvent("hero_primary_cta_clicked", { source: "hero" })}
            >
              <IconText icon="rocket">{LP_CTA.primary}</IconText>
            </Link>
            <Link
              href="#curriculum-download"
              className={uiStyles.actionGhost}
              onClick={() => trackLpEvent("curriculum_download_clicked", { source: "hero" })}
            >
              <IconText icon="notebookText">{LP_CTA.secondary}</IconText>
            </Link>
          </div>
        </div>

        <div className={styles.heroVisual}>
          <HeroMock reducedMotion={reducedMotion} />
        </div>
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
        <Section title={LP_SOLUTION_SECTION.title} meta={LP_SOLUTION_SECTION.meta}>
          <div className={styles.valueGrid}>
            {LP_SOLUTION_SECTION.values.map((prop) => (
              <article key={prop.id} className={styles.valueCard}>
                <span className={styles.valueIconBadge}>
                  <AppIcon name={prop.icon} size={16} />
                </span>
                <h3>{prop.title}</h3>
                <p>{prop.body}</p>
              </article>
            ))}
          </div>
          <p className={styles.valueFootnote}>{LP_SOLUTION_SECTION.footnote}</p>
        </Section>
      </div>

      <div id="stakeholders" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section
          title="経営・DX推進・人材開発・事業部門が、同じ成果物で意思決定できる"
          meta="複数部門が関与するB2B購買で、各部門に刺さる導入価値を整理します。"
        >
          <StakeholderValueTabs reducedMotion={reducedMotion} />
        </Section>
      </div>

      <div id="demo" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title={LP_PRODUCT_DEMO.title} meta={LP_PRODUCT_DEMO.meta}>
          <ProductDemoTabs reducedMotion={reducedMotion} />
        </Section>
      </div>

      <div id="curriculum" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone4}`}>
        <Section
          title="12週間で、AI活用アイデアをPoC計画・実装ロードマップまで引き上げる"
          meta="各Weekで成果物を残し、最終週に経営・部門向け提案へ接続します。"
        >
          <CurriculumTimeline reducedMotion={reducedMotion} />
        </Section>
      </div>

      <div id="roles" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section
          title="部門や役割に合わせて、7つのAI人材トラックを設計"
          meta="受講者の職種や部門に応じて、ロール別の学習モジュールと成果物を割り当てます。"
        >
          <RoleTracksSection />
        </Section>
      </div>

      <div id="deliverables" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section
          title="受講完了ではなく、AIプロジェクト化に必要な成果物を残す"
          meta="研修のゴールは学習ログではなく、経営・部門が判断できる資料です。"
        >
          <div id="sample-deliverables">
            <DeliverablesPreview />
          </div>
          <div className={styles.deliverablesCta}>
            <Link
              href="#sample-deliverables"
              className={uiStyles.actionGhost}
              onClick={() => trackLpEvent("sample_deliverable_clicked", { source: "deliverables_section" })}
            >
              <IconText icon="fileCheck2">{LP_CTA.tertiary}</IconText>
            </Link>
          </div>
        </Section>
      </div>

      <div id="review" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section
          title="提出して終わりではなく、実務品質までレビューする"
          meta="AIレビューとメンターレビューの二段構えで、経営判断に使える品質まで引き上げます。"
        >
          <ReviewSystemSection />
        </Section>
      </div>

      <div id="use-cases" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone4}`}>
        <Section title={LP_USE_CASES.title} meta={LP_USE_CASES.meta}>
          <UseCasesSection />
        </Section>
      </div>

      <div data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section title="AIリテラシー研修ではなく、AIプロジェクトを生み出す実践プログラム" meta="一般的なAI研修との比較です。">
          <ComparisonTable4 />
        </Section>
      </div>

      <div id="pricing" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section title="目的に合わせて、AI人材育成からPoC創出まで段階導入" meta="企業規模・目的別の導入プランです。">
          <PricingPackages />
        </Section>
      </div>

      <div id="implementation" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title="まずは1部門・1テーマから、無理なく開始できます" meta="導入から成果発表までの標準フローです。">
          <ImplementationFlowSection />
        </Section>
      </div>

      <div id="faq" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section title="FAQ" meta="導入検討時によくいただく質問です。">
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
              trackLpEvent("hero_primary_cta_clicked", { source: "final_cta" });
              trackLpEvent("final_cta_clicked", { cta: "diagnosis" });
            }}
          >
            <IconText icon="rocket">{LP_FINAL_CTA.primaryCta}</IconText>
          </Link>
          <Link
            href="#curriculum-download"
            className={uiStyles.actionGhost}
            onClick={() => {
              trackLpEvent("curriculum_download_clicked", { source: "final_cta" });
              trackLpEvent("final_cta_clicked", { cta: "curriculum" });
            }}
          >
            {LP_FINAL_CTA.secondaryCta}
          </Link>
        </div>
      </section>

      <div id="curriculum-download" className={styles.srOnly} aria-hidden>
        カリキュラム資料請求フォーム（導入相談へ接続）
      </div>

      <StickyCtaBar />
    </main>
  );
}
