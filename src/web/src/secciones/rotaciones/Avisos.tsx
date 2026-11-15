// asistido por SI: Claude Code (Anthropic), avisos del gemelo; el primero siempre se ve
export function Avisos({ avisos }: { avisos: string[] }) {
  if (avisos.length === 0) return null
  const [primero, ...resto] = avisos
  return (
    <div className="avisos">
      <p role="note" className="aviso-principal" data-testid="aviso-gemelo" data-texto-gemelo="">{primero}</p>
      {resto.length > 0 && <ul>{resto.map((a) => <li key={a} data-texto-gemelo="">{a}</li>)}</ul>}
    </div>
  )
}
