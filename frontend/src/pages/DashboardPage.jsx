import { StatusCard } from '../components/StatusCard/StatusCard';
import { SystemInfo } from '../components/SystemInfo/SystemInfo';
import { ProductionData } from '../components/ProductionData/ProductionData';
import { TemperatureData } from '../components/TemperatureData/TemperatureData';
import { PositionData } from '../components/PositionData/PositionData';

export function DashboardPage({ data }) {
  return (
    <div className="dashboard-grid">
      <StatusCard 
        status={data.status}
        alarms={data.alarms}
        hasAlarms={data.has_alarms}
      />
      
      <div className="sidebar-section">
        <SystemInfo 
          softwareName={data.software_name}
          softwareVersion={data.software_version}
        />
        
        <PositionData 
          trianglePosition={data.triangle_position}
          centerSealingPosition={data.center_sealing_position}
        />
      </div>
      
      <div className="main-section">
        <ProductionData 
          recipe={data.recipe}
          totalPieces={data.total_pieces}
          partialPieces={data.partial_pieces}
          batchCounter={data.batch_counter}
        />
        
        <TemperatureData 
          lateralBarTemp={data.lateral_bar_temp}
          frontalBarTemp={data.frontal_bar_temp}
        />
      </div>
    </div>
  );
}