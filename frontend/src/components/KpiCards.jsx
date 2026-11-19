function KpiCards({ kpis, loading, onPick }) {
  if (loading) {
    return (
      <section className="kpis">
        {[0, 1, 2, 3].map((i) => <div key={i} className="kpi glass skeleton" />)}
      </section>
    )
  }
  if (!kpis.length) return null

  return (
    <section className="kpis">
      {kpis.map((k) => (
        <button key={k.key} className="kpi glass" onClick={() => onPick(k.message)}
                title={`Ask: ${k.message}`}>
          <span className="kpi-label">{k.label}</span>
          <span className="kpi-value">{k.value}</span>
          <span className="kpi-hint">{k.hint}</span>
        </button>
      ))}
    </section>
  )
}

export default KpiCards