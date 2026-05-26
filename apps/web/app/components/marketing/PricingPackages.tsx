"use client";

import Link from "next/link";

import { AppIcon } from "@/app/components/ui";
import uiStyles from "@/app/components/ui/ui.module.css";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_PRICING } from "./lpContent";

export function PricingPackages() {
  return (
    <div className={styles.pricingGrid}>
      {LP_PRICING.plans.map((plan) => {
        const cardClass = `${styles.pricingCard} ${plan.highlight ? styles.pricingCardHighlight : ""}`;
        return (
          <article key={plan.id} className={cardClass}>
            {plan.highlight ? (
              <span className={styles.pricingRecommendBadge}>営業強化におすすめ</span>
            ) : null}
            <h3>{plan.title}</h3>
            <p className={styles.pricingPurpose}>{plan.audience}</p>
            <ul className={styles.pricingInclude}>
              {plan.includes.map((item) => (
                <li key={item}>
                  <AppIcon name="checkCircle2" size={14} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p className={styles.pricingPrice}>{plan.price}</p>
            <Link
              href="/business/sign-up"
              className={plan.highlight ? uiStyles.actionPrimary : uiStyles.actionGhost}
              onClick={() => trackLpEvent("pricing_plan_clicked", { plan: plan.id })}
            >
              {plan.cta}
            </Link>
          </article>
        );
      })}
    </div>
  );
}
