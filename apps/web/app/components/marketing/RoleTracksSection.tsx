"use client";

import { useState } from "react";

import { AppIcon } from "@/app/components/ui";

import { trackLpEvent } from "@/lib/lp-analytics";

import styles from "./aiFieldReadyLanding.module.css";
import { LP_ROLE_TRACKS } from "./lpContent";

const INITIAL_VISIBLE = 4;

export function RoleTracksSection() {
  const [expanded, setExpanded] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  const visibleTracks = expanded ? LP_ROLE_TRACKS : LP_ROLE_TRACKS.slice(0, INITIAL_VISIBLE);
  const activeTrack = LP_ROLE_TRACKS.find((t) => t.id === activeId);

  return (
    <div className={styles.roleTracks}>
      <div className={styles.roleGrid}>
        {visibleTracks.map((track) => (
          <button
            key={track.id}
            type="button"
            className={`${styles.roleCard} ${styles.roleCardInteractive} ${activeId === track.id ? styles.roleCardActive : ""}`}
            onClick={() => {
              setActiveId(activeId === track.id ? null : track.id);
              trackLpEvent("role_track_opened", { role: track.id });
            }}
          >
            <AppIcon name="target" size={16} />
            <span>{track.role}</span>
          </button>
        ))}
      </div>

      {!expanded && LP_ROLE_TRACKS.length > INITIAL_VISIBLE ? (
        <button
          type="button"
          className={styles.roleExpandButton}
          onClick={() => setExpanded(true)}
        >
          すべてのロールを見る（{LP_ROLE_TRACKS.length}種）
        </button>
      ) : null}

      {activeTrack ? (
        <article className={styles.roleTrackDetail}>
          <header>
            <h3>{activeTrack.role}</h3>
            <p>主対象: {activeTrack.audience}</p>
          </header>
          <p className={styles.roleTrackGoal}>{activeTrack.goal}</p>
          <div className={styles.roleTrackColumns}>
            <div>
              <h4>学習モジュール</h4>
              <ul>
                {activeTrack.modules.map((m) => (
                  <li key={m}>{m}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4>主な成果物</h4>
              <ul>
                {activeTrack.deliverables.map((d) => (
                  <li key={d}>{d}</li>
                ))}
              </ul>
            </div>
          </div>
        </article>
      ) : null}
    </div>
  );
}
