type DiffRow = {
  field: string;
  before: string;
  after: string;
};

export function CurriculumDiffViewer({
  rows,
  updateType
}: {
  rows: DiffRow[];
  updateType: "minor" | "major" | "breaking";
}) {
  return (
    <section>
      <h2>差分確認</h2>
      <p className="muted">更新種別: {updateType}</p>
      {rows.length === 0 ? (
        <p className="muted">差分はありません。</p>
      ) : (
        <ul className="card-list">
          {rows.map((row) => (
            <li key={row.field}>
              <strong>{row.field}</strong>
              <p className="muted">before: {row.before || "(empty)"}</p>
              <p className="muted">after: {row.after || "(empty)"}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
