/**
 * AI Field Ready Enterprise LP の共有コンテンツ定義。
 *
 * 事業会社向け AI 人材育成・AI プロジェクト創出プログラムの文言を一元管理し、
 * クライアント側コンポーネントとサーバー側 JSON-LD の両方から再利用する。
 */

import type { AppIconName } from "@/app/components/ui";

export const LP_BRAND = {
  name: "AI Field Ready Enterprise",
  tagline: "事業会社向け｜AI人材育成・AIプロジェクト創出"
} as const;

export const LP_SEO = {
  title: "AI Field Ready Enterprise｜事業会社向けAI人材育成・AIプロジェクト創出プログラム",
  description:
    "自社の業務課題を起点に、AIテーマ化からPoC計画・実装ロードマップまで伴走する、事業会社向け実践型AI人材育成プログラム。"
} as const;

export const LP_HEADER_NAV: Array<{ href: string; label: string }> = [
  { href: "#challenges", label: "課題" },
  { href: "#solution", label: "特徴" },
  { href: "#curriculum", label: "カリキュラム" },
  { href: "#deliverables", label: "成果物" },
  { href: "#pricing", label: "導入" },
  { href: "#faq", label: "FAQ" }
];

export const LP_CTA = {
  primary: "AI人材育成診断を相談する",
  secondary: "カリキュラム資料を見る",
  tertiary: "サンプル成果物を見る"
} as const;

export const LP_HERO = {
  badge: "事業会社向け｜AI人材育成・AIプロジェクト創出",
  heading: "AIを学ぶ研修で終わらせない。\n自社の業務課題から、AIプロジェクトを生み出せる人材を育てる。",
  subcopy: "業務課題の定義からPoC計画・実装ロードマップまで、12週間で伴走する実践型プログラムです。"
} as const;

export const LP_CHALLENGE_SECTION = {
  title: "AI研修をしても、現場のAIプロジェクトが生まれない理由",
  meta: "問われるのは受講完了ではなく、社内からAIプロジェクトが生まれるかです。",
  beforeAfter: {
    before: "研修後も適用テーマが出ない",
    after: "PoC計画つきテーマが現場から出る"
  },
  items: [
    {
      title: "研修がリテラシーで止まる",
      body: "使い方は学んでも、自社業務への適用設計ができない"
    },
    {
      title: "部門からAIテーマが出ない",
      body: "課題・KPI・データ・制約を整理する型がない"
    },
    {
      title: "PoC計画に落ちない",
      body: "検証範囲・成功条件・評価指標が曖昧なまま止まる"
    }
  ]
} as const;

export const LP_SOLUTION_SECTION = {
  title: "業務課題を、AIプロジェクト候補へ変える",
  meta: "意思決定に使える成果物まで作り切ります。",
  values: [
    {
      id: "issue-driven",
      title: "業務課題起点",
      body: "自社の業務・KPI・データを題材にする",
      icon: "target" as AppIconName
    },
    {
      id: "deliverable-driven",
      title: "成果物駆動",
      body: "課題定義書・PoC計画書など判断材料を残す",
      icon: "fileCheck2" as AppIconName
    },
    {
      id: "projectization",
      title: "プロジェクト化支援",
      body: "PoC候補・実装ロードマップへ接続する",
      icon: "rocket" as AppIconName
    }
  ]
} as const;

export const LP_TRUST_SECTION = {
  title: "実践型カリキュラムの設計根拠",
  meta: "業務課題起点・成果物駆動の設計は、現場のAIプロジェクト創出プロセスに基づいています。",
  body:
    "AI Field Ready Enterpriseの教材設計・評価基準は、事業会社でのAI活用プロジェクト（業務課題定義、PoC設計、評価、運用）の実務フローをベースに構築しています。",
  pillars: [
    "業務課題定義とKPI設計",
    "AIテーマ化と優先度設計",
    "RAG / AI-OCR / データ分析 / エージェント活用",
    "PoC計画と評価指標設計",
    "プロトタイプ検証と改善ループ",
    "ガバナンスとリスク評価",
    "経営向けAIプロジェクト提案",
    "実装ロードマップ設計"
  ],
  note: "詳細実績は秘密保持の範囲で個別にご案内します。"
} as const;

export const LP_STAKEHOLDER_TABS: Array<{
  id: string;
  label: string;
  audience: string;
  benefit: string;
  detail: string;
  icon: AppIconName;
}> = [
  {
    id: "exec",
    label: "経営層",
    audience: "経営層",
    benefit: "AI投資テーマを、研修後の成果物として可視化できる",
    detail:
      "PoC候補、費用対効果仮説、実装ロードマップを経営判断資料として提示。研修投資が次のAIプロジェクト化につながるかを定量的に把握できます。",
    icon: "chart"
  },
  {
    id: "dx",
    label: "DX推進",
    audience: "DX推進部門",
    benefit: "各部門のAI活用テーマを、PoC候補として整理・比較できる",
    detail:
      "部門横断でAIテーマ候補を一覧化し、効果・実現性・データ準備度で優先順位付け。推進すべきPoCを選定する共通フレームを提供します。",
    icon: "layoutDashboard"
  },
  {
    id: "hr",
    label: "人材開発",
    audience: "人材開発部門",
    benefit: "受講率ではなく、業務課題定義・PoC計画・提案書を育成成果にできる",
    detail:
      "学習ログではなく成果物の提出・レビュー・承認をKPI化。研修の実務接続と成果の可視化を同時に実現します。",
    icon: "users"
  },
  {
    id: "business",
    label: "事業部門",
    audience: "事業部門",
    benefit: "自部門の業務課題を題材に、実際に使えるAI施策を設計できる",
    detail:
      "汎用教材ではなく自部門のAs-Is業務とKPIを起点に演習。現場が主語のAI活用テーマを社内から生み出せます。",
    icon: "building2"
  },
  {
    id: "it",
    label: "情シス/法務",
    audience: "情報システム / 法務",
    benefit: "セキュリティ、データ利用、承認フローを早期に組み込める",
    detail:
      "データ棚卸し、利用ルール、リスク評価をカリキュラム初期から設計。ガバナンス抜けのPoCを防ぎます。",
    icon: "shieldCheck"
  }
];

export const LP_PRODUCT_DEMO = {
  title: "問い合わせ回答支援AIの操作感",
  meta: "業務課題登録からPoC計画まで、CS題材での画面の流れを短く確認できます。"
} as const;

export const LP_CURRICULUM_TIMELINE = {
  title: "12週間で、アイデアをPoC計画・実装ロードマップまで引き上げる",
  meta: "各フェーズで成果物を残し、最終週に提案へ接続します。",
  phases: [
    {
      week: "Week 0-1",
      label: "診断・基礎",
      body: "課題・受講者・データ状況を把握し、全体像を共有します。",
      deliverable: "初期診断レポート"
    },
    {
      week: "Week 2-4",
      label: "課題定義",
      body: "業務フロー・KPI・制約とデータ／ナレッジを棚卸しします。",
      deliverable: "業務課題定義書"
    },
    {
      week: "Week 5-10",
      label: "演習・PoC",
      body: "仮説・成功条件・評価指標を設計し、プロトタイプで検証します。",
      deliverable: "PoC計画書・検証ログ"
    },
    {
      week: "Week 11-12",
      label: "提案・実装計画",
      body: "評価をまとめ、経営／部門向け提案と実装計画につなげます。",
      deliverable: "AIプロジェクト提案書"
    }
  ],
  roleLabels: [
    "AIプロダクト企画",
    "業務改善",
    "RAG/ナレッジ",
    "データ分析",
    "AIエージェント",
    "AI-OCR",
    "AIガバナンス"
  ]
} as const;

export const LP_ROLE_TRACKS: Array<{
  id: string;
  role: string;
  audience: string;
  goal: string;
  modules: string[];
  deliverables: string[];
}> = [
  {
    id: "product",
    role: "AIプロダクト企画人材",
    audience: "事業企画、DX推進、PdM候補",
    goal: "業務課題をAIプロダクト企画・PoC計画に変換できる",
    modules: ["AIプロダクト企画", "ユーザー/業務要求整理", "PoC設計", "経営向け提案"],
    deliverables: ["AIテーマ企画書", "PoC計画書", "AIプロジェクト提案書"]
  },
  {
    id: "improvement",
    role: "AI業務改善リーダー",
    audience: "事業部門、業務改善担当",
    goal: "現場業務を分析し、生成AI/自動化による改善案を設計できる",
    modules: ["業務プロセス分析", "生成AI活用設計", "効果測定", "現場定着"],
    deliverables: ["業務フロー図", "生成AI活用設計書", "運用手順書"]
  },
  {
    id: "rag",
    role: "RAG/ナレッジ活用推進人材",
    audience: "情シス、総務、人事、CS",
    goal: "社内文書・FAQ・マニュアルをRAG活用できる状態に整理・評価できる",
    modules: ["RAG基礎", "文書棚卸し", "チャンク設計", "回答評価", "運用設計"],
    deliverables: ["RAG検証計画", "検索評価表", "RAG運用設計書"]
  },
  {
    id: "data",
    role: "データ分析/BI人材",
    audience: "経営企画、営業企画、マーケ",
    goal: "業務データを分析し、意思決定や改善施策につなげられる",
    modules: ["データ分析基礎", "SQL/データ抽出", "KPIダッシュボード", "仮説検証"],
    deliverables: ["分析レポート", "ダッシュボード設計書"]
  },
  {
    id: "agent",
    role: "AIエージェント活用人材",
    audience: "DX推進、情シス、業務企画",
    goal: "複数ツール/APIを組み合わせた業務自動化フローを設計できる",
    modules: ["エージェント基礎", "業務分解", "ツール連携", "人間介在設計"],
    deliverables: ["自動化/エージェント設計書", "エージェントPoC計画書"]
  },
  {
    id: "ocr",
    role: "AI-OCR/文書自動化人材",
    audience: "経理、総務、法務",
    goal: "帳票・文書処理の抽出設計、精度評価、例外処理設計ができる",
    modules: ["AI-OCR基礎", "帳票分類", "抽出項目定義", "精度評価", "例外処理"],
    deliverables: ["OCR検証レポート", "例外処理フロー"]
  },
  {
    id: "governance",
    role: "AIガバナンス推進人材",
    audience: "法務、情シス、リスク管理",
    goal: "AI利用ルール、リスク評価、承認フロー、評価基準を整備できる",
    modules: ["AIリスク基礎", "利用ルール設計", "評価/監査", "プロジェクト審査"],
    deliverables: ["AI利用ガイドライン", "AIプロジェクト審査フロー"]
  }
];

export const LP_DELIVERABLES_SECTION = {
  eyebrow: "Deliverables",
  title: "判断に使える成果物を残す",
  meta: "CSの問い合わせ業務を題材に、課題定義から提案書まで作り切ります。",
  items: [
    { name: "業務課題定義書", use: "一次回答フローとKPIを整理" },
    { name: "AIテーマ候補リスト", use: "FAQ検索／回答ドラフトを優先順位付け" },
    { name: "PoC計画書", use: "対象・成功条件・評価指標を定義" },
    { name: "評価レポート", use: "時間・品質・根拠・リスクを評価" },
    { name: "AIプロジェクト提案書", use: "経営・部門向けの意思決定資料" }
  ],
  preview: {
    title: "AIプロジェクト提案書（サンプル）",
    theme: "問い合わせ回答支援AI",
    department: "カスタマーサポート",
    issue: "初回回答が長い（FAQ手検索がボトルネック）",
    approach: "RAG + 回答ドラフト生成（人が最終確認）",
    successCriteria: "回答作成時間30%削減・根拠提示率90%",
    nextAction: "2か月PoC（製品問い合わせに限定）",
    asIs: {
      label: "As-Is",
      kpi: "平均初回回答 8時間",
      process: "FAQを手検索し、回答を一から作成"
    },
    toBe: {
      label: "To-Be",
      kpi: "根拠付きドラフト → 人が最終確認",
      process: "AIが関連FAQ／マニュアルを検索し、回答案と根拠を提示"
    },
    dataSources: ["製品FAQ", "操作マニュアル", "過去問い合わせ（マスキング済）"],
    outOfScope: ["個人情報を含む問い合わせ", "補償・返金の個別判断", "クレームの感情対応"],
    guardrails: ["根拠必須表示", "人が最終送信", "対象外はエスカレーション"],
    sampleDrafts: [
      {
        category: "返品・交換",
        inquiry: "返品期限後でも初期不良なら交換できますか？",
        draft: "初期不良が確認できれば期限後も交換可能です。購入日・型番・不具合内容を添えてご連絡ください。",
        sources: ["FAQ #12", "保証ガイド p.4"],
        disposition: "一次回答可"
      },
      {
        category: "補償判断",
        inquiry: "修理対応で破損した周辺機器の補償をお願いします。",
        draft: "個別の補償判断が必要なため担当部門へ引き継ぎます。2営業日以内にご連絡します。",
        sources: ["エスカレーション基準"],
        disposition: "エスカレーション"
      }
    ]
  }
} as const;

export const LP_REVIEW_SYSTEM = {
  title: "提出して終わりではなく、実務品質までレビューする",
  meta: "メンターレビューで提出物を確認します。AI採点は現在準備中です。",
  reviews: [
    { type: "AI採点（準備中）", body: "検証済みの評価器の接続後に提供予定です。現在は自動合格判定を行いません" },
    { type: "メンターレビュー", body: "実務観点で、業務適合性、PoC実現性、評価設計、運用性を確認" },
    { type: "改善履歴", body: "再提出、改善コメント、承認状態を記録" },
    { type: "成果物承認", body: "PoC候補や経営提案に使える水準かを判定" }
  ],
  rubric: [
    { axis: "業務課題の具体性", body: "課題、対象業務、KPI、関係者が具体化されているか" },
    { axis: "AI適用の妥当性", body: "AIで解くべき理由と、人が担うべき部分が整理されているか" },
    { axis: "データ準備度", body: "利用データ、品質、権限、更新頻度が把握されているか" },
    { axis: "PoC設計力", body: "検証範囲、成功条件、評価指標が明確か" },
    { axis: "ガバナンス", body: "セキュリティ、個人情報、運用リスクが考慮されているか" },
    { axis: "提案力", body: "経営/部門が判断できる資料になっているか" }
  ]
} as const;

export const LP_USE_CASES = {
  title: "製造・小売・物流・金融・バックオフィスまで、業務課題をAIテーマ化",
  meta: "業種・部門ごとの適用例。自社の業務課題にも転用できるフレームです。",
  cases: [
    {
      industry: "カスタマーサポート",
      theme: "問い合わせ回答支援AI、FAQ検索、エスカレーション判定",
      deliverable: "回答ドラフト評価、PoC計画書、運用ガードレール"
    },
    { industry: "製造業", theme: "保全マニュアル検索、検査記録分析、品質異常検知", deliverable: "RAG検証計画、品質分析レポート" },
    { industry: "小売/EC", theme: "需要予測、在庫分析、問い合わせ対応AI", deliverable: "データ分析レポート、FAQ/RAG設計書" },
    { industry: "物流", theme: "配送遅延分析、作業日報要約、倉庫業務自動化", deliverable: "業務改善設計書、自動化フロー" },
    { industry: "金融/保険", theme: "文書審査支援、社内ナレッジ検索、リスクチェック", deliverable: "文書処理検証レポート、リスク評価表" },
    { industry: "人事/総務", theme: "社内問い合わせAI、規程検索、申請業務自動化", deliverable: "RAG設計書、運用ルール案" },
    { industry: "経理/法務", theme: "請求書OCR、契約書レビュー補助、文書分類", deliverable: "AI-OCR検証レポート、例外処理設計" }
  ]
} as const;

export const LP_COMPARISON = {
  title: "AIリテラシー研修ではなく、AIプロジェクトを生み出す実践プログラム",
  meta: "一般的なAI研修・eラーニング・コンサル依存型PoCとの比較です。",
  columns: ["一般的なAI研修", "eラーニング", "コンサル依存型PoC", "AI Field Ready Enterprise"],
  rows: [
    { label: "起点", values: ["AI知識", "教材", "外部コンサルの提案", "自社業務課題"] },
    { label: "成果", values: ["受講完了、理解度テスト", "視聴履歴", "コンサル作成資料", "受講者自身が作るPoC計画・提案書"] },
    { label: "対象", values: ["全社員向けが中心", "個人学習中心", "一部プロジェクトメンバー", "部門横断のAI推進人材"] },
    { label: "業務接続", values: ["弱い", "弱い", "外部依存しやすい", "業務課題・データ・制約まで整理"] },
    { label: "レビュー", values: ["講義後アンケート中心", "自動テスト中心", "コンサルレビュー", "メンターレビュー（AI採点は準備中）"] },
    { label: "研修後", values: ["実務接続が課題", "継続率が課題", "内製化しにくい", "PoC候補・実装ロードマップへ接続"] }
  ]
} as const;

export const LP_PRICING = {
  title: "目的に合わせて段階導入",
  meta: "まずは小さく始め、必要に応じて拡張できます。",
  plans: [
    {
      id: "diagnosis",
      title: "AI人材育成診断",
      audience: "まず課題と対象者を整理したい企業",
      includes: ["部門ヒアリング", "受講者診断", "育成方針案"],
      price: "無料〜30万円",
      cta: "相談する",
      highlight: false
    },
    {
      id: "standard",
      title: "12週間標準プログラム",
      audience: "PoC候補まで作りたい企業",
      includes: ["課題定義", "ロール別演習", "PoC計画", "成果発表"],
      price: "200万〜500万円",
      cta: "相談する",
      highlight: true
    },
    {
      id: "custom",
      title: "個別カスタム",
      audience: "自社データ・業務に合わせたい企業",
      includes: ["独自教材", "閉域環境", "実装支援接続"],
      price: "個別見積",
      cta: "相談する",
      highlight: false
    }
  ]
} as const;

export const LP_IMPLEMENTATION_FLOW = [
  { step: 1, title: "無料相談・課題ヒアリング", body: "現状のAI活用状況、対象部門、育成したい人材像を把握", period: "30〜60分" },
  { step: 2, title: "AI人材育成診断", body: "部門ヒアリング、受講者診断、育成方針案を作成", period: "1〜2週間" },
  { step: 3, title: "対象部門・受講者・テーマ候補の決定", body: "業務課題とロール別トラックを確定", period: "1週間" },
  { step: 4, title: "カリキュラム開始", body: "教材学習、演習提出、AI/メンターレビューを実施", period: "4〜12週間" },
  { step: 5, title: "成果発表・PoC候補選定", body: "AIプロジェクト提案書と実装ロードマップを提示", period: "最終週" },
  { step: 6, title: "PoC/実装ロードマップ検討", body: "次フェーズのPoC化・本番化判断へ接続", period: "次フェーズ" }
] as const;

export const LP_ROLES = LP_ROLE_TRACKS.map((t) => t.role);

export const LP_FAQS: Array<{ q: string; a: string; defaultOpen?: boolean }> = [
  {
    q: "一般的な生成AI研修と何が違いますか？",
    a: "リテラシー習得ではなく、自社業務課題からPoC計画・提案書まで作成する実践型プログラムです。",
    defaultOpen: true
  },
  {
    q: "プログラミング経験がない社員でも参加できますか？",
    a: "可能です。企画・業務改善・ガバナンスなど、非コーディングのロールにも対応しています。"
  },
  {
    q: "どの部門が対象ですか？",
    a: "事業部門、DX推進、情シス、人材開発、経営企画、法務、CSなど部門横断です。現場担当者の参加が特に効果的です。"
  },
  {
    q: "サンプルの「問い合わせ回答支援AI」は必須テーマですか？",
    a: "必須ではありません。CS一次回答の具体例です。自社課題に置き換え、同じ型で進めます。"
  },
  {
    q: "研修後に残る成果物は？",
    a: "業務課題定義書、AIテーマ候補、PoC計画書、評価レポート、AIプロジェクト提案書などです。"
  },
  {
    q: "自社の業務課題やデータを使えますか？",
    a: "はい。機密情報の扱いは導入時に確認し、必要なら閉域環境で対応します。"
  },
  {
    q: "短期実施やPoC支援は可能ですか？",
    a: "4週間トライアルや個別カスタムでのPoC伴走にも対応できます。まずは診断相談から。"
  }
];

export const LP_FINAL_CTA = {
  eyebrow: "Get Started",
  title: "まずは1部門・1テーマから始められます",
  body: "AI活用状況と育成したい人材像を伺い、進め方をご提案します。",
  primaryCta: LP_CTA.primary,
  secondaryCta: LP_CTA.secondary
} as const;
