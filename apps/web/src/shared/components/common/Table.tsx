import React from 'react';

interface Column<T> {
  header: string;
  accessor: (item: T) => React.ReactNode;
  style?: React.CSSProperties;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  isLoading?: boolean;
  emptyMessage?: string;
}

export default function Table<T>({
  data,
  columns,
  isLoading = false,
  emptyMessage = 'No records found.',
}: TableProps<T>) {
  return (
    <div style={styles.wrapper}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.headerRow}>
            {columns.map((col, idx) => (
              <th key={idx} style={{ ...styles.th, ...col.style }}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading &&
            Array.from({ length: 3 }).map((_, rIdx) => (
              <tr key={rIdx} style={styles.row}>
                {columns.map((_, cIdx) => (
                  <td key={cIdx} style={styles.td}>
                    <div style={styles.skeleton} />
                  </td>
                ))}
              </tr>
            ))}

          {!isLoading && data.length === 0 && (
            <tr>
              <td colSpan={columns.length} style={styles.emptyCell}>
                {emptyMessage}
              </td>
            </tr>
          )}

          {!isLoading &&
            data.map((item, rIdx) => (
              <tr key={rIdx} style={styles.row}>
                {columns.map((col, cIdx) => (
                  <td key={cIdx} style={{ ...styles.td, ...col.style }}>
                    {col.accessor(item)}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    width: '100%',
    overflowX: 'auto',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--color-surface)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
    fontSize: '14px',
  },
  headerRow: {
    borderBottom: '1px solid var(--color-border)',
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
  },
  th: {
    padding: '16px 20px',
    color: 'var(--color-text-secondary)',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    fontSize: '13px',
    textTransform: 'uppercase',
  },
  row: {
    borderBottom: '1px solid var(--color-border)',
    transition: 'background-color 150ms ease',
  },
  td: {
    padding: '16px 20px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-body)',
  },
  emptyCell: {
    padding: '32px',
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
  },
  skeleton: {
    height: '16px',
    backgroundColor: 'var(--color-border)',
    borderRadius: 'var(--radius-sm)',
    width: '80%',
    animation: 'pulse 1.5s infinite ease-in-out',
  },
};
