import { useEffect, useState } from 'react';
import './App.css';

type Cell = {
  row: number;
  column: number;
  value: number | null;
};

type Restriction = {
  cell: string;
  operator: '>' | '<';
  value: number;
};

type Capacity = {
  cell: string;
  value: number;
};

function App() {
  const [rows, setRows] = useState(3);
  const [cols, setCols] = useState(3);
  const [tableData, setTableData] = useState<Cell[][]>([]);
  const [suppliers, setSuppliers] = useState<number[]>([]);
  const [consumers, setConsumers] = useState<number[]>([]);
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  const [capacities, setCapacities] = useState<Capacity[]>([]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).particlesJS.load('particles-js', '/particles-config.json', () => {
        console.log('particles.js loaded');
      });
    }

    return () => {
      if ((window as any).pJSDom && (window as any).pJSDom.length) {
        (window as any).pJSDom[0].pJS.fn.vendors.destroy();
      }
    };
  }, []);

  const handleCellChange = (rowIndex: number, colIndex: number, value: number | null) => {
    setTableData(prev => {
      const newData = [...prev];
      newData[rowIndex] = newData[rowIndex] || [];
      newData[rowIndex][colIndex] = { row: rowIndex, column: colIndex, value };
      return newData;
    });
  };

  return (
    <div className={'app dark-theme'}>
      <div id="particles-js"></div>
      
      <header>
      <h1>Transport Problem Solver</h1>
    </header>

      <div className="controls">
        <div className="input-group">
          <label>Suppliers:</label>
          <input 
            type="number" 
            value={rows} 
            onChange={(e) => setRows(Number(e.target.value))}
            min={1}
          />
        </div>
        
        <div className="input-group">
          <label>Consumers:</label>
          <input 
            type="number" 
            value={cols} 
            onChange={(e) => setCols(Number(e.target.value))}
            min={1}
          />
        </div>
      </div>

      <div className="table-container">
        <div className="transport-table">
          <div className="table-header">
            <div className="corner-cell"></div>
            {Array.from({ length: cols }, (_, i) => (
              <div key={i} className="header-cell">
                Consumer {i + 1}
                <input 
                  type="number" 
                  placeholder="Demand"
                  value={consumers[i] || ''}
                  onChange={(e) => {
                    const newConsumers = [...consumers];
                    newConsumers[i] = Number(e.target.value);
                    setConsumers(newConsumers);
                  }}
                />
              </div>
            ))}
          </div>

          <div className="table-body">
            {Array.from({ length: rows }, (_, rowIndex) => (
              <div key={rowIndex} className="table-row">
                <div className="supplier-cell">
                  Supplier {rowIndex + 1}
                  <input 
                    type="number" 
                    placeholder="Supply"
                    value={suppliers[rowIndex] || ''}
                    onChange={(e) => {
                      const newSuppliers = [...suppliers];
                      newSuppliers[rowIndex] = Number(e.target.value);
                      setSuppliers(newSuppliers);
                    }}
                  />
                </div>
                
                {Array.from({ length: cols }, (_, colIndex) => (
                  <input
                    key={colIndex}
                    type="number"
                    className="table-cell"
                    value={tableData[rowIndex]?.[colIndex]?.value || ''}
                    onChange={(e) => {
                      const value = e.target.value ? parseFloat(e.target.value) : null;
                      handleCellChange(rowIndex, colIndex, value);
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="additional-controls">
        <div className="restrictions">
          <h3>Restrictions</h3>
          {restrictions.map((r, i) => (
            <div key={i} className="restriction-item">
              <select 
                value={r.cell} 
                onChange={(e) => {
                  const newRestrictions = [...restrictions];
                  newRestrictions[i].cell = e.target.value;
                  setRestrictions(newRestrictions);
                }}
              >
                {tableData.flat().map(cell => (
                  <option key={`${cell.row}-${cell.column}`} value={`${cell.row}-${cell.column}`}>
                    Cell ({cell.row + 1}, {cell.column + 1})
                  </option>
                ))}
              </select>
              <select 
                value={r.operator}
                onChange={(e) => {
                  const newRestrictions = [...restrictions];
                  newRestrictions[i].operator = e.target.value as '>' | '<';
                  setRestrictions(newRestrictions);
                }}
              >
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
              </select>
              <input 
                type="number" 
                value={r.value}
                onChange={(e) => {
                  const newRestrictions = [...restrictions];
                  newRestrictions[i].value = Number(e.target.value);
                  setRestrictions(newRestrictions);
                }}
              />
            </div>
          ))}
          <button onClick={() => setRestrictions([...restrictions, { cell: '0-0', operator: '>', value: 0 }])}>
            Add Restriction
          </button>
        </div>

        <div className="capacities">
          <h3>Capacities</h3>
          {capacities.map((c, i) => (
            <div key={i} className="capacity-item">
              <select 
                value={c.cell} 
                onChange={(e) => {
                  const newCapacities = [...capacities];
                  newCapacities[i].cell = e.target.value;
                  setCapacities(newCapacities);
                }}
              >
                {tableData.flat().map(cell => (
                  <option key={`${cell.row}-${cell.column}`} value={`${cell.row}-${cell.column}`}>
                    Cell ({cell.row + 1}, {cell.column + 1})
                  </option>
                ))}
              </select>
              <input 
                type="number" 
                value={c.value}
                onChange={(e) => {
                  const newCapacities = [...capacities];
                  newCapacities[i].value = Number(e.target.value);
                  setCapacities(newCapacities);
                }}
              />
            </div>
          ))}
          <button onClick={() => setCapacities([...capacities, { cell: '0-0', value: 0 }])}>
            Add Capacity
          </button>
        </div>
      </div>

      <button className="solve-button">Solve</button>
    </div>
  );
}

export default App;