type ConsentCardProps = {
  title: string;
  purpose: string;
  scope: string;
  dataTarget: string;
  onAccept: () => void;
};

export function ConsentCard({
  title,
  purpose,
  scope,
  dataTarget,
  onAccept
}: ConsentCardProps) {
  return (
    <div className="consent-card">
      <h3>{title}</h3>
      <p>利用目的: {purpose}</p>
      <p>提供範囲: {scope}</p>
      <p>対象データ: {dataTarget}</p>
      <p className="muted">同意はいつでも取り消し可能です。</p>
      <button type="button" onClick={onAccept}>
        同意する
      </button>
    </div>
  );
}
