/**
 * AI Field Ready Enterprise LP の共有コンテンツ定義。
 *
 * 事業会社向け AI 人材育成・AI プロジェクト創出プログラムの文言を一元管理し、
 * クライアント側コンポーネントとサーバー側 JSON-LD の両方から再利用する。
 */

import type { AppIconName } from "@/app/components/ui";

export const LP_BRAND = {
  name: "AI Field Ready Enterprise",
  tagline: "事業会社向け｜AI人材育成・AIプロジェクト創出プログラム"
} as const;

export const LP_SEO = {
  title: "AI Field Ready Enterprise｜事業会社向けAI人材育成・AIプロジェクト創出プログラム",
  description:
    "AI Field Ready Enterpriseは、事業会社向けの実践型AI人材育成プログラムです。自社の業務課題を起点に、AIテーマ化、PoC設計、プロトタイプ検証、評価レポート、実装ロードマップ作成までを支援します。生成AI研修で終わらせず、AIプロジェクトを社内から生み出す人材を育成します。"
} as const;

export const LP_HEADER_NAV: Array<{ href: string; label: string }> = [
  { href: "#challenges", label: "課題" },
  { href: "#solution", label: "特徴" },
  { href: "#curriculum", label: "カリキュラム" },
  { href: "#deliverables", label: "成果物" },
  { href: "#pricing", label: "導入プラン" },
  { href: "#faq", label: "FAQ" }
];

export const LP_CTA = {
  primary: "AI人材育成診断を相談する",
  secondary: "カリキュラム資料を見る",
  tertiary: "サンプル成果物を見る"
} as const;

export const LP_HERO = {
  badge: "事業会社向け｜AI人材育成・AIプロジェクト創出プログラム",
  heading: "AIを学ぶ研修で終わらせない。\n自社の業務課題から、AIプロジェクトを生み出せる人材を育てる。",
  subcopy:
    "AI Field Ready Enterpriseは、業務課題定義、AIテーマ化、PoC設計、プロトタイプ検証、評価レポート、実装ロードマップ作成までを一気通貫で支援する、事業会社向けの実践型AI人材育成プログラムです。",
  trustMicrocopy: "AIリテラシー研修ではなく、部門課題からPoC候補を作る実践プログラムです。",
  beforeAfter: {
    before: "生成AI研修を受けたが、現場業務への適用テーマが出てこない",
    after: "各部門から、PoC計画書・評価指標・実装ロードマップつきのAIテーマが出てくる"
  }
} as const;

export const LP_CHALLENGE_SECTION = {
  title: "AI研修を実施しても、現場のAIプロジェクトが生まれない理由",
  meta: "研修完了率ではなく、社内からAIプロジェクトが生まれるかが問われる時代に。",
  items: [
    {
      title: "研修がAIリテラシーで止まる",
      body: "生成AIの使い方は学んでも、自社業務のどこに適用すべきか設計できない"
    },
    {
      title: "各部門からAIテーマが出てこない",
      body: "現場課題、KPI、データ状況、制約を整理する型がない"
    },
    {
      title: "PoC計画に落とし込めない",
      body: "アイデアは出るが、検証範囲、成功条件、評価指標、体制が曖昧なまま止まる"
    },
    {
      title: "情シス/法務/現場の共通言語がない",
      body: "セキュリティ、データ利用、運用、リスクの観点が後回しになる"
    },
    {
      title: "研修成果が経営判断に使えない",
      body: "受講完了率やテストスコアだけでは、次の投資判断につながらない"
    }
  ]
} as const;

export const LP_SOLUTION_SECTION = {
  title: "業務課題を、AIプロジェクト候補へ変える実践型カリキュラム",
  meta: "学習完了ではなく、意思決定に使える成果物を残すプログラム設計です。",
  footnote:
    "AIを「使える人」を増やすだけでは不十分です。必要なのは、自社の業務課題を見極め、AIで解くべきテーマを選び、検証計画まで作れる人材です。",
  values: [
    {
      id: "issue-driven",
      title: "業務課題起点",
      body: "自社の業務フロー、KPI、データ、制約を題材にするため、研修が現場課題に直結する",
      icon: "target" as AppIconName
    },
    {
      id: "deliverable-driven",
      title: "成果物駆動",
      body: "受講完了ではなく、業務課題定義書、AIテーマ企画書、PoC計画書、評価レポートを作成する",
      icon: "fileCheck2" as AppIconName
    },
    {
      id: "projectization",
      title: "プロジェクト化支援",
      body: "研修後に、PoC候補、実装ロードマップ、運用設計、経営提案へ接続する",
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
  title: "業務課題からPoC計画まで、カリキュラム内で作り切る",
  meta: "実際のSaaS画面に近いUIで、業務課題登録から成果物レビューまでの流れを確認できます。"
} as const;

export const LP_CURRICULUM_TIMELINE = {
  title: "12週間で、AI活用アイデアをPoC計画・実装ロードマップまで引き上げる",
  meta: "各フェーズで必ず成果物を残し、最終週に経営・部門向け提案へ接続します。",
  phases: [
    { week: "Week 0", label: "事前診断", body: "企業課題、受講者、部門、データ状況の把握", deliverable: "初期診断レポート" },
    { week: "Week 1", label: "AI/DX共通基礎", body: "生成AI、RAG、AI-OCR、AIエージェント、分析の全体像", deliverable: "AI活用アイデアシート" },
    { week: "Week 2-3", label: "業務課題定義", body: "業務フロー、KPI、制約、関係者整理", deliverable: "業務課題定義書" },
    { week: "Week 4", label: "データ/ナレッジ棚卸し", body: "データ品質、文書、権限、機密情報整理", deliverable: "データ/文書棚卸し表" },
    { week: "Week 5-8", label: "ロール別実務演習", body: "RAG、分析、OCR、自動化、エージェント等", deliverable: "演習提出物、レビュー履歴" },
    { week: "Week 9", label: "PoC設計", body: "検証仮説、成功条件、評価指標、体制", deliverable: "PoC計画書" },
    { week: "Week 10", label: "プロトタイプ/検証", body: "簡易デモ、評価表、改善案作成", deliverable: "プロトタイプ、検証ログ" },
    { week: "Week 11", label: "評価・改善", body: "技術、業務、セキュリティ、運用評価", deliverable: "評価レポート、改善計画" },
    { week: "Week 12", label: "成果発表/実装計画", body: "経営/部門向け提案、次期計画", deliverable: "AIプロジェクト提案書" }
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
  title: "受講完了ではなく、AIプロジェクト化に必要な成果物を残す",
  meta: "研修のゴールは学習ログではなく、経営・部門が判断できる資料です。",
  items: [
    { name: "AI活用アイデアシート", use: "各部門のAI活用候補を洗い出す" },
    { name: "業務課題定義書", use: "As-Is業務、課題、KPI、制約を整理する" },
    { name: "AIテーマ候補リスト", use: "AIで解くべきテーマを分類・優先順位付けする" },
    { name: "データ/文書棚卸し表", use: "AI活用に必要なデータ・文書の状態を把握する" },
    { name: "PoC計画書", use: "検証範囲、成功条件、評価指標、体制を定義する" },
    { name: "プロトタイプ/検証ログ", use: "実際の検証結果や改善点を残す" },
    { name: "評価レポート", use: "技術・業務・セキュリティ・運用面から評価する" },
    { name: "AIプロジェクト提案書", use: "経営/部門向けの意思決定資料にする" },
    { name: "実装ロードマップ", use: "PoC後の本番化・運用定着計画を示す" }
  ],
  preview: {
    title: "AIプロジェクト提案書",
    theme: "問い合わせ回答支援AI",
    department: "カスタマーサポート",
    issue: "初回回答時間が長い、回答品質にばらつきがある",
    approach: "RAG + 回答ドラフト生成",
    successCriteria: "回答作成時間30%削減、回答根拠提示率90%",
    data: "FAQ、マニュアル、問い合わせ履歴",
    risks: "個人情報、誤回答、更新運用",
    nextAction: "2か月PoC、対象業務限定、評価体制構築"
  }
} as const;

export const LP_REVIEW_SYSTEM = {
  title: "提出して終わりではなく、実務品質までレビューする",
  meta: "AIレビューとメンターレビューの二段構えで、経営判断に使える品質まで引き上げます。",
  reviews: [
    { type: "AIレビュー", body: "テンプレートの抜け漏れ、論理構成、評価指標、リスク記載を一次確認" },
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
    { label: "レビュー", values: ["講義後アンケート中心", "自動テスト中心", "コンサルレビュー", "AIレビュー＋メンターレビュー"] },
    { label: "研修後", values: ["実務接続が課題", "継続率が課題", "内製化しにくい", "PoC候補・実装ロードマップへ接続"] }
  ]
} as const;

export const LP_PRICING = {
  title: "目的に合わせて、AI人材育成からPoC創出まで段階導入",
  meta: "企業規模・目的別の導入プラン。まずは小さく始めて段階的に拡張できます。",
  plans: [
    {
      id: "diagnosis",
      title: "AI人材育成診断",
      audience: "まず課題と対象者を整理したい企業",
      includes: ["部門ヒアリング", "受講者診断", "育成方針案", "AIテーマ候補の初期整理"],
      price: "無料〜30万円",
      cta: "自社に合うプランを相談する",
      highlight: false
    },
    {
      id: "trial",
      title: "4週間トライアル",
      audience: "小さく検証したい部門",
      includes: ["AI基礎", "業務課題定義", "AIテーマ候補作成", "経営向けテーマ提案"],
      price: "50万〜100万円",
      cta: "自社に合うプランを相談する",
      highlight: false
    },
    {
      id: "standard",
      title: "12週間標準プログラム",
      audience: "PoC候補まで作りたい企業",
      includes: ["共通基礎", "課題定義", "ロール別演習", "PoC計画", "成果発表"],
      price: "200万〜500万円",
      cta: "自社に合うプランを相談する",
      highlight: true
    },
    {
      id: "cross-dept",
      title: "部門横断プログラム",
      audience: "複数部門で展開したい企業",
      includes: ["複数トラック", "メンター伴走", "成果発表会", "経営提案"],
      price: "500万〜1,500万円",
      cta: "自社に合うプランを相談する",
      highlight: false
    },
    {
      id: "custom",
      title: "個別カスタム",
      audience: "自社データ/業務に合わせたい企業",
      includes: ["独自教材", "閉域環境", "ガバナンス対応", "実装支援接続"],
      price: "個別見積",
      cta: "自社に合うプランを相談する",
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
    a: "一般的な研修はAIの使い方やリテラシー習得が中心ですが、AI Field Ready Enterpriseは、自社の業務課題を起点に、AIテーマ企画書、PoC計画書、評価レポート、実装ロードマップまで作成する実践型プログラムです。",
    defaultOpen: true
  },
  {
    q: "プログラミング経験がない社員でも参加できますか？",
    a: "参加可能です。ロール別トラックにより、AIプロダクト企画や業務改善、ガバナンスなど、コーディングを主としない役割にも対応しています。技術トラックについては基礎から段階的に学べる設計です。",
    defaultOpen: true
  },
  {
    q: "どの部門の社員が対象になりますか？",
    a: "事業部門、DX推進、情シス、人材開発、経営企画、法務など、部門横断で参加いただけます。自部門の業務課題を題材にするため、現場担当者の参加が特に効果的です。"
  },
  {
    q: "研修後にはどのような成果物が残りますか？",
    a: "業務課題定義書、AIテーマ候補リスト、データ/文書棚卸し表、PoC計画書、評価レポート、AIプロジェクト提案書、実装ロードマップなど、意思決定に使える成果物が残ります。"
  },
  {
    q: "自社の業務課題やデータを使えますか？",
    a: "はい。本プログラムは自社の業務課題・データ・制約を起点に設計します。機密情報の取り扱いについては、導入時にガバナンス方針を確認し、必要に応じて閉域環境等で対応します。"
  },
  {
    q: "機密情報や個人情報がある場合はどう対応しますか？",
    a: "データ棚卸し段階で機密区分・利用可否を整理し、AIガバナンストラックで利用ルールと承認フローを設計します。個別カスタムプランでは閉域環境への対応も可能です。"
  },
  {
    q: "AIレビューだけで評価するのですか？",
    a: "いいえ。AIレビューは一次評価であり、重要な成果物はメンター/講師による実務レビューと承認を行います。AIは反応速度と網羅性を、メンターは実務妥当性を担保します。"
  },
  {
    q: "4週間など短期での実施は可能ですか？",
    a: "可能です。4週間トライアルでは業務課題定義からAIテーマ候補作成までを集中して実施し、経営向けテーマ提案まで到達します。"
  },
  {
    q: "人材開発部門主導でも導入できますか？",
    a: "はい。人材開発部門主導の導入が多く、研修成果を成果物ベースで可視化できる点が評価されています。DX推進部門との共同運用も一般的です。"
  },
  {
    q: "PoCや実装支援まで依頼できますか？",
    a: "個別カスタムプランでPoC設計・プロトタイプ伴走・技術レビュー・実装支援接続まで対応可能です。まずは12週間標準プログラムでPoC候補を具体化する導入が一般的です。"
  },
  {
    q: "既存のLMSや社内研修と併用できますか？",
    a: "併用可能です。既存の基礎研修を活かしつつ、業務課題起点の演習・成果物作成・レビューをAI Field Ready Enterprise側で担う構成が一般的です。"
  },
  {
    q: "オンライン/対面/ハイブリッドに対応できますか？",
    a: "はい。オンデマンド教材とライブワークショップを組み合わせ、オンライン・対面・ハイブリッドいずれでも実施可能です。"
  }
];

export const LP_FINAL_CTA = {
  eyebrow: "Get Started",
  title: "自社の業務課題から、AIプロジェクトを生み出せる人材を育てませんか？",
  body: "まずは1部門・1テーマから開始できます。現在のAI活用状況、対象部門、育成したい人材像を伺い、最適なカリキュラムと進め方をご提案します。",
  primaryCta: LP_CTA.primary,
  secondaryCta: LP_CTA.secondary
} as const;
