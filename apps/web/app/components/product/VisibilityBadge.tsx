type VisibilityMode = "non_public" | "limited" | "public" | "anonymous";

const LABEL_MAP: Record<VisibilityMode, string> = {
  non_public: "非公開",
  limited: "限定公開",
  public: "公開",
  anonymous: "匿名公開"
};

export function VisibilityBadge({ mode }: { mode: VisibilityMode }) {
  return <span className={`visibility-badge visibility-${mode}`}>{LABEL_MAP[mode]}</span>;
}
