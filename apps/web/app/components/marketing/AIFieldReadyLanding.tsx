"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppIcon, IconText } from "@/app/components/ui";
import { Section } from "@/app/components/ui/Section";
import uiStyles from "@/app/components/ui/ui.module.css";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { CurriculumTimeline } from "./CurriculumTimeline";
import { DeliverablesPreview } from "./DeliverablesPreview";
import { FaqSection } from "./FaqSection";
import { HeroMock } from "./HeroMock";
import {
  LP_BRAND,
  LP_CHALLENGE_SECTION,
  LP_CTA,
  LP_CURRICULUM_TIMELINE,
  LP_DELIVERABLES_SECTION,
  LP_FINAL_CTA,
  LP_HEADER_NAV,
  LP_HERO,
  LP_PRICING,
  LP_PRODUCT_DEMO,
  LP_SOLUTION_SECTION
} from "./lpContent";
import { PricingPackages } from "./PricingPackages";
import { ProductDemoTabs } from "./ProductDemoTabs";
import { StickyCtaBar } from "./StickyCtaBar";

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
            href="/business/sign-up"
            className={uiStyles.actionPrimary}
            onClick={() => trackLpEvent("hero_primary_cta_clicked", { source: "header" })}
          >
            <IconText icon="rocket">診断を相談</IconText>
          </Link>
          <Link href="/auth/sign-in" className={styles.loginLink}>
            ログイン（学習者・企業）
          </Link>
        </div>
      </header>

      <section
        className={`${uiStyles.hero} ${uiStyles.heroMarketing} ${styles.hero} ${styles.heroSplit}`}
        data-reveal="section"
      >
        <div className={styles.heroContent}>
          <p className={styles.heroBrand}>{LP_BRAND.name}</p>
          <h1 className={`${uiStyles.heroTitle} ${styles.heroTitle}`}>
            {heroLines.map((line, i) => (
              <span key={line}>
                {line}
                {i < heroLines.length - 1 ? <br /> : null}
              </span>
            ))}
          </h1>
          <p className={styles.heroLead}>{LP_HERO.subcopy}</p>

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
          <ol className={styles.challengeList}>
            {LP_CHALLENGE_SECTION.items.map((challenge, index) => (
              <li key={challenge.title} className={styles.challengeItem}>
                <span className={styles.challengeIndex}>0{index + 1}</span>
                <div>
                  <h3>{challenge.title}</h3>
                  <p>{challenge.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <p className={styles.challengeBridge}>
            <span className={styles.challengeBridgeLabel}>Before</span>
            {LP_CHALLENGE_SECTION.beforeAfter.before}
            <span className={styles.challengeBridgeArrow} aria-hidden>
              →
            </span>
            <span className={styles.challengeBridgeLabel}>After</span>
            {LP_CHALLENGE_SECTION.beforeAfter.after}
          </p>
        </Section>
      </div>

      <div id="solution" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section title={LP_SOLUTION_SECTION.title} meta={LP_SOLUTION_SECTION.meta}>
          <ol className={styles.valueList}>
            {LP_SOLUTION_SECTION.values.map((prop, index) => (
              <li key={prop.id} className={styles.valueListItem}>
                <span className={styles.valueListIndex} aria-hidden>
                  0{index + 1}
                </span>
                <span className={styles.valueIconBadge}>
                  <AppIcon name={prop.icon} size={16} />
                </span>
                <div>
                  <h3>{prop.title}</h3>
                  <p>{prop.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </Section>
      </div>

      <div id="product-demo" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section title={LP_PRODUCT_DEMO.title} meta={LP_PRODUCT_DEMO.meta}>
          <ProductDemoTabs reducedMotion={reducedMotion} compact />
        </Section>
      </div>

      <div id="curriculum" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone4}`}>
        <Section title={LP_CURRICULUM_TIMELINE.title} meta={LP_CURRICULUM_TIMELINE.meta}>
          <CurriculumTimeline reducedMotion={reducedMotion} />
          <div className={styles.roleChipRow} aria-label="育成ロール">
            <p className={styles.roleChipLabel}>育成ロール例</p>
            <ul className={styles.roleChips}>
              {LP_CURRICULUM_TIMELINE.roleLabels.map((role) => (
                <li key={role}>{role}</li>
              ))}
            </ul>
          </div>
        </Section>
      </div>

      <div id="deliverables" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone3}`}>
        <Section title={LP_DELIVERABLES_SECTION.title} meta={LP_DELIVERABLES_SECTION.meta}>
          <div id="sample-deliverables">
            <DeliverablesPreview />
          </div>
        </Section>
      </div>

      <div id="pricing" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone1}`}>
        <Section title={LP_PRICING.title} meta={LP_PRICING.meta}>
          <PricingPackages />
        </Section>
      </div>

      <div id="faq" data-reveal="section" className={`${styles.revealSection} ${styles.sectionTone2}`}>
        <Section title="FAQ" meta="導入検討時のよくある質問です。">
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
