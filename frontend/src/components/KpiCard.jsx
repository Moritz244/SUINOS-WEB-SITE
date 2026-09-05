export function KpiCard({ label, value, unit, sub, accent = "emerald", icon: Icon, testId }) {
  const accentClass = {
    emerald: "kpi-accent-emerald",
    aqua: "kpi-accent-aqua",
    amber: "kpi-accent-amber",
  }[accent] || "";
  const iconBg = {
    emerald: "bg-emerald-50 text-emerald-600",
    aqua: "bg-sky-50 text-sky-600",
    amber: "bg-amber-50 text-amber-600",
  }[accent];

  return (
    <div className={`kpi-card ${accentClass}`} data-testid={testId}>
      <div className="flex items-start justify-between mb-3">
        <div className="text-xs sm:text-sm font-semibold uppercase tracking-wider text-slate-500">
          {label}
        </div>
        {Icon && (
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="font-display font-black text-3xl sm:text-4xl lg:text-5xl tracking-tight text-slate-900 leading-none">
        {value}
        {unit && <span className="text-base sm:text-lg font-semibold text-slate-500 ml-1.5">{unit}</span>}
      </div>
      {sub && <div className="mt-2 text-sm text-slate-500">{sub}</div>}
    </div>
  );
}
