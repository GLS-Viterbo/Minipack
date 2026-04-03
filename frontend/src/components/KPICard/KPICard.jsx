import './KPICard.css';

export function KPICard({ title, value, unit, icon: Icon, trend, color = 'blue' }) {
  return (
    <div className={`kpi-card kpi-card-${color}`}>
      <div className="kpi-card-header">
        {Icon && <Icon size={24} className="kpi-icon" />}
        <h3 className="kpi-title">{title}</h3>
      </div>
      <div className="kpi-content">
        <div className="kpi-value">
          {value}
          {unit && <span className="kpi-unit">{unit}</span>}
        </div>
        {trend && (
          <div className={`kpi-trend kpi-trend-${trend.direction}`}>
            {trend.text}
          </div>
        )}
      </div>
    </div>
  );
}