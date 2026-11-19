// Turns a status word into one of four quiet tones.
function tone(value) {
  const t = String(value).toLowerCase()
  if (/^(paid|approved|delivered|present|received)/.test(t)) return 'ok'
  if (/^(pending|unpaid)/.test(t)) return 'warn'
  if (/^(rejected|cancelled|absent|overdue)/.test(t)) return 'bad'
  return 'neutral'
}

const isMoney = (v) => /^-?₹/.test(String(v))

function DataTable({ table }) {
  const { columns, rows } = table
  const statusCol = columns.findIndex((c) => c.toLowerCase() === 'status')

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, i) => (
                <td key={i} className={`${i === 0 ? 'first' : ''} ${isMoney(cell) ? 'num' : ''}`}>
                  {i === statusCol
                    ? <span className={`badge ${tone(cell)}`}>{cell}</span>
                    : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default DataTable