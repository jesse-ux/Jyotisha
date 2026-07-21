export type ParameterFreezeRow = {
  label: string;
  value: string;
};

export function ParameterFreezePanel({ rows }: { readonly rows: readonly ParameterFreezeRow[] }) {
  return (
    <section className="parameter-freeze-panel" aria-label="当前排盘参数冻结">
      <div>
        <b>当前排盘参数</b>
        <span>这些参数会随咨询一起送入证据链。</span>
      </div>
      <dl>
        {rows.map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
