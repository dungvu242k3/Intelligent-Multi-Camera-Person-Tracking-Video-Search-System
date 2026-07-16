import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartDataPoint {
  time: string;
  detections: number;
  alarms: number;
}

interface ActivityChartProps {
  data: ChartDataPoint[];
  title: string;
}

export default function ActivityChart({ data, title }: ActivityChartProps) {
  return (
    <div className="card" style={styles.card}>
      <h3 style={styles.title}>{title}</h3>
      <div style={styles.chartContainer}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorDetections" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorAlarms" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-danger)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="var(--color-danger)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.3} />
            <XAxis
              dataKey="time"
              stroke="var(--color-text-secondary)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="var(--color-text-secondary)"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--color-surface)',
                borderColor: 'var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text)',
                fontFamily: 'var(--font-body)',
              }}
            />
            <Area
              type="monotone"
              dataKey="detections"
              stroke="var(--color-primary)"
              fillOpacity={1}
              fill="url(#colorDetections)"
              name="Person Detections"
            />
            <Area
              type="monotone"
              dataKey="alarms"
              stroke="var(--color-danger)"
              fillOpacity={1}
              fill="url(#colorAlarms)"
              name="Safety Alarms"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    padding: '24px',
    height: '350px',
  },
  title: {
    fontSize: '16px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  chartContainer: {
    flex: 1,
    width: '100%',
    height: '100%',
    minHeight: '200px',
  },
};
