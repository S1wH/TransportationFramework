import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ParticlesBackground from './ParticlesBackground';
import { FullTable } from './types';
import './App.css';

enum SolveMethods {
  northwest = 1,
  min_cost,
  vogel,
}

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

type Root = {
  supplier_id: number;
  consumer_id: number;
  amount: number;
  epsilon: number;
};

type SolutionResponse = {
  price: number;
  is_optimal: boolean;
  roots: Root[];
};

interface TableComponentProps {
  tableData: Cell[][];
  restrictions: Restriction[];
  capacities: Capacity[];
  setRestrictions: (restrictions: Restriction[]) => void;
  setCapacities: (capacities: Capacity[]) => void;
}

// Restrictions and Capacities components remain unchanged
function Restrictions({ tableData, restrictions, setRestrictions }: TableComponentProps) {
  const updateRestriction = (index: number, field: keyof Restriction, value: string | number) => {
    const newRestrictions = [...restrictions];
    newRestrictions[index] = { ...newRestrictions[index], [field]: value };
    setRestrictions(newRestrictions);
  };

  const deleteRestriction = (index: number) => {
    setRestrictions(restrictions.filter((_, i) => i !== index));
  };

  return (
    <div className="restrictions">
      <h3>Restrictions</h3>
      <div className="controls-list">
        {restrictions.map((restriction, index) => (
          <div key={index} className="restriction-item">
            <select
              value={restriction.cell}
              onChange={(e) => updateRestriction(index, 'cell', e.target.value)}
            >
              {tableData.flat().map((cell) => (
                <option key={`${cell.row}-${cell.column}`} value={`${cell.row}-${cell.column}`}>
                  Cell ({cell.row + 1}, {cell.column + 1})
                </option>
              ))}
            </select>
            <select
              value={restriction.operator}
              onChange={(e) => updateRestriction(index, 'operator', e.target.value as '>' | '<')}
            >
              <option value=">">&gt;</option>
              <option value="<">&lt;</option>
            </select>
            <input
              type="number"
              value={restriction.value}
              onChange={(e) => updateRestriction(index, 'value', Number(e.target.value))}
            />
            <button className="delete-button" onClick={() => deleteRestriction(index)}>
              ×
            </button>
          </div>
        ))}
      </div>
      <button
        className="add-button"
        onClick={() => setRestrictions([...restrictions, { cell: '0-0', operator: '>', value: 0 }])}
      >
        Add Restriction
      </button>
    </div>
  );
}

function Capacities({ tableData, capacities, setCapacities }: TableComponentProps) {
  const allCells = tableData.flat();
  const occupiedCells = new Set(capacities.map((c) => c.cell));

  const updateCapacity = (index: number, field: keyof Capacity, value: string | number) => {
    const newCapacities = [...capacities];
    newCapacities[index] = { ...newCapacities[index], [field]: value };
    setCapacities(newCapacities);
  };

  const addCapacity = () => {
    const availableCells = allCells.filter((cell) => !occupiedCells.has(`${cell.row}-${cell.column}`));
    if (availableCells.length > 0) {
      setCapacities([...capacities, { cell: `${availableCells[0].row}-${availableCells[0].column}`, value: 0 }]);
    }
  };

  const deleteCapacity = (index: number) => {
    setCapacities(capacities.filter((_, i) => i !== index));
  };

  return (
    <div className="capacities">
      <h3>Capacities</h3>
      <div className="controls-list">
        {capacities.map((capacity, index) => {
          const availableCells = allCells.filter(
            (cell) =>
              !occupiedCells.has(`${cell.row}-${cell.column}`) ||
              `${cell.row}-${cell.column}` === capacity.cell
          );
          return (
            <div key={index} className="capacity-item">
              <select
                value={capacity.cell}
                onChange={(e) => updateCapacity(index, 'cell', e.target.value)}
              >
                {availableCells.map((cell) => (
                  <option key={`${cell.row}-${cell.column}`} value={`${cell.row}-${cell.column}`}>
                    Cell ({cell.row + 1}, {cell.column + 1})
                  </option>
                ))}
              </select>
              <input
                type="number"
                value={capacity.value}
                onChange={(e) => updateCapacity(index, 'value', Number(e.target.value))}
              />
              <button className="delete-button" onClick={() => deleteCapacity(index)}>
                ×
              </button>
            </div>
          );
        })}
      </div>
      <button
        className="add-button"
        onClick={addCapacity}
        disabled={allCells.length === capacities.length}
      >
        Add Capacity
      </button>
    </div>
  );
}

interface TransportSolverProps {
  userId: string | null;
  onLogout: () => void;
}

const validateTableData = (
  tableData: Cell[][],
  suppliers: number[],
  consumers: number[],
  rows: number,
  cols: number
): string | null => {
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      if (!tableData[i]?.[j]?.value && tableData[i]?.[j]?.value !== 0) {
        return `All cells must be filled (missing value at row ${i + 1}, column ${j + 1})`;
      }
    }
  }

  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      if (tableData[i]?.[j]?.value < 0) {
        return `Cell values must be equal to or greater than 0 (negative value at row ${i + 1}, column ${j + 1})`;
      }
    }
  }

  for (let i = 0; i < cols; i++) {
    if (suppliers[i] <= 0 || suppliers[i] === undefined) {
      return `Supplier ${i + 1} must have a value greater than 0`;
    }
  }

  for (let i = 0; i < rows; i++) {
    if (consumers[i] <= 0 || consumers[i] === undefined) {
      return `Consumer ${i + 1} must have a value greater than 0`;
    }
  }

  return null;
};

const TransportSolver: React.FC<TransportSolverProps> = ({ userId, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [rows, setRows] = useState(3);
  const [cols, setCols] = useState(3);
  const [tableData, setTableData] = useState<Cell[][]>([]);
  const [suppliers, setSuppliers] = useState<number[]>([]);
  const [consumers, setConsumers] = useState<number[]>([]);
  const [restrictions, setRestrictions] = useState<Restriction[]>([]);
  const [capacities, setCapacities] = useState<Capacity[]>([]);
  const [capacityError, setCapacityError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [solutionData, setSolutionData] = useState<SolutionResponse | null>(null);
  const [isSolving, setIsSolving] = useState(false);
  const [method, setMethod] = useState<'northwest' | 'min_cost' | 'vogel'>('northwest');
  const [tableId, setTableId] = useState<number | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [isNotificationVisible, setIsNotificationVisible] = useState(false);
  const [isLoadingTable, setIsLoadingTable] = useState(true);

  useEffect(() => {
    if (location.state?.tableData) {
      setIsLoadingTable(true);
      const table: FullTable = location.state.tableData;
      const { id, suppliers, consumers, price_matrix, restrictions: serverRestrictions, capacities } = table;

      // Set table ID
      setTableId(id);

      // Set rows and columns based on the table dimensions
      setRows(suppliers.length);
      setCols(consumers.length);


      // Set suppliers and consumers
      setSuppliers(suppliers);
      setConsumers(consumers);

      // Convert price_matrix to tableData format
      const newTableData = price_matrix.map((row, rowIndex) =>
        row.map((value, colIndex) => ({
          row: rowIndex,
          column: colIndex,
          value: value ?? 0, // Ensure no null values
        }))
      );
      setTableData(newTableData);

      // Parse restrictions from server format to component format
      const parsedRestrictions = Object.entries(serverRestrictions).map(([key, value]) => {
        const [row, col] = key.split(',').map(s => s.trim());
        const operator = value[0] as '>' | '<';
        const val = Number(value.slice(1));
        return { cell: `${row}-${col}`, operator, value: val };
      });
      setRestrictions(parsedRestrictions);

      // Set capacities (already in the correct format)
      setCapacities(capacities);

      // Optional: Notify user that the table was loaded
      setNotification(`Loaded table: ${table.name}`);
    }
    else{
        setIsLoadingTable(false);
    }
  }, [location.state]);

  // Notification effect
  useEffect(() => {
    if (notification) {
      setIsNotificationVisible(true);
      const timer = setTimeout(() => {
        setIsNotificationVisible(false);
        setNotification(null); // Clear notification after hiding
      }, 2700);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // Capacity error check
  useEffect(() => {
    const errorMsg =
      capacities.length > 0 && capacities.length !== rows * cols
        ? 'All cells must have capacities when capacities are defined'
        : '';
    setCapacityError(errorMsg);
    if (errorMsg) setNotification(errorMsg);
  }, [capacities, rows, cols]);

  // Adjust data when rows/cols change
  useEffect(() => {
    if (isLoadingTable) return;

    const adjustData = (data: any[], maxLength: number) =>
      data.filter((_, i) => i < maxLength).map((item) => item || 0);

    setSuppliers((prev) => adjustData(prev, rows));
    setConsumers((prev) => adjustData(prev, cols));
    setRestrictions((prev) =>
      prev.filter((r) => {
        const [row, col] = r.cell.split('-').map(Number);
        return row < rows && col < cols;
      })
    );
    setCapacities((prev) =>
      prev.filter((c) => {
        const [row, col] = c.cell.split('-').map(Number);
        return row < rows && col < cols;
      })
    );

    const newTableData = Array.from({ length: rows }, (_, row) =>
      Array.from({ length: cols }, (_, col) => ({
        row,
        column: col,
        value: tableData[row]?.[col]?.value ?? 0,
      }))
    );
    setTableData(newTableData);
    }, [rows, cols, isLoadingTable]);

  const getSolutionGrid = (): (string | number)[][] => {
    if (!solutionData?.roots) return Array(rows).fill(Array(cols).fill(0));
    const grid = Array.from({ length: rows }, () => Array(cols).fill(0));
    solutionData.roots.forEach((root) => {
      const { supplier_id: supplierId, consumer_id: consumerId, amount, epsilon } = root;
      grid[supplierId][consumerId] = epsilon
        ? `${amount || ''}${epsilon > 0 ? '+' : '-'}${Math.abs(epsilon)}ε`
        : amount;
    });
    return grid;
  };

  const updateCell = (row: number, col: number, value: number | null) => {
    const newValue = value !== null && value < 0 ? 0 : value;
    setTableData((prev) => {
      const newData = [...prev];
      newData[row] = [...newData[row]];
      newData[row][col] = { row, column: col, value: newValue };
      return newData;
    });
  };

  const convertRestrictions = (restrictions: Restriction[]): Record<string, string> =>
    restrictions.reduce((acc, { cell, operator, value }) => {
      const [row, col] = cell.split('-').map(Number);
      acc[`${row}, ${col}`] = `${operator}${value}`;
      return acc;
    }, {} as Record<string, string>);

  const solvePlan = async (type: 'basic' | 'optimal') => {
    // Validate table data
    const validationError = validateTableData(tableData, suppliers, consumers, rows, cols);
    if (validationError) {
      setNotification(validationError);
      return;
    }

    if (capacityError) {
      setNotification(capacityError);
      return;
    }

    setIsSolving(true);
    const priceMatrix = Array.from({ length: rows }, (_, i) =>
      Array.from({ length: cols }, (_, j) => tableData[i][j].value)
    );

    const payload = {
      suppliers,
      consumers,
      price_matrix: priceMatrix,
      restrictions: restrictions.length ? convertRestrictions(restrictions) : null,
      capacities: capacities.length ? capacities : null,
      ...(type === 'basic' && { method }),
      ...(userId && { user_id: userId }),
      user_id: userId,
    };

    const method_type = SolveMethods[method];
    const url = `http://127.0.0.1:8000/tables/create_${type}_plan/?mode=${method_type}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to solve: ${errorText || 'Unknown error'}`);
      }
      const result = await response.json();
      setSolutionData(result);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Solve error:', error);
      setNotification(`Error solving ${type} plan: ${error.message}`);
    } finally {
      setIsSolving(false);
    }
  };

  const handleSaveSolution = async () => {
    if (!userId) {
      setNotification('You need to log in to save the solution');
      return;
    }

    if (!solutionData) {
      setNotification('No solution to save');
      return;
    }

    try {
      let currentTableId = tableId;

      if (currentTableId === null) {
        const priceMatrix = Array.from({ length: rows }, (_, i) =>
          Array.from({ length: cols }, (_, j) => tableData[i]?.[j]?.value ?? 0)
        );

        const createTablePayload = {
          user_id: userId,
          rows: rows,
          cols: cols,
          price_matrix: priceMatrix,
          suppliers: suppliers.map((s) => s || 0),
          consumers: consumers.map((c) => c || 0),
          restrictions: restrictions.length ? convertRestrictions(restrictions) : null,
          capacities: capacities.length ? capacities : null,
        };

        const createResponse = await fetch('http://127.0.0.1:8000/tables/create/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(createTablePayload),
        });

        if (!createResponse.ok) {
          const errorText = await createResponse.text();
          throw new Error(`Failed to create table: ${errorText || 'Unknown error'}`);
        }

        const createData = await createResponse.json();
        currentTableId = createData;
        setTableId(currentTableId);
      }

      const saveSolutionPayload = {
        price: solutionData.price,
        is_optimal: solutionData.is_optimal,
        roots: solutionData.roots,
      };

      const saveResponse = await fetch(
        `http://127.0.0.1:8000/tables/save_solution/${currentTableId}/?user_id=${userId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(saveSolutionPayload),
        }
      );

      if (!saveResponse.ok) {
        const errorText = await saveResponse.text();
        throw new Error(`Failed to save solution: ${errorText || 'Unknown error'}`);
      }

      setNotification('Solution saved successfully');
    } catch (error) {
      console.error('Error saving solution:', error);
      setNotification(`Error saving solution: ${error.message}`);
    }
  };

  return (
    <div className="app dark-theme">
      <ParticlesBackground />

      {userId ? (
        <div className="user-profile">
          <div className="profile-avatar">
            <span>TP</span>
          </div>
          <div className="profile-menu">
            <button onClick={() => navigate('/tables')}>Tables</button>
            <button onClick={onLogout}>Logout</button>
          </div>
        </div>
      ) : (
        <div className="auth-buttons">
          <button className="login-button" onClick={() => navigate('/login')}>
            Log In
          </button>
          <button className="register-button" onClick={() => navigate('/register')}>
            Register
          </button>
        </div>
      )}

      <div className="controls-container">
        <Restrictions
          tableData={tableData}
          restrictions={restrictions}
          setRestrictions={setRestrictions}
          capacities={capacities}
          setCapacities={setCapacities}
        />
        <Capacities
          tableData={tableData}
          capacities={capacities}
          setCapacities={setCapacities}
          restrictions={restrictions}
          setRestrictions={setRestrictions}
        />
      </div>

      <div className="table-container">
        <div className="transport-table-wrapper">
          <div className="table-header" style={{ gridTemplateColumns: `150px repeat(${cols}, minmax(80px, 1fr))` }}>
            <div className="corner-cell">
              <div className="control">
                <label>Suppliers</label>
                <div className="number-control">
                  <button onClick={() => setRows(Math.max(1, rows - 1))}>-</button>
                  <input
                    type="number"
                    value={rows}
                    onChange={(e) => setRows(Math.max(1, Number(e.target.value)))}
                    min={1}
                  />
                  <button onClick={() => setRows(rows + 1)}>+</button>
                </div>
              </div>
              <div className="control">
                <label>Consumers</label>
                <div className="number-control">
                  <button onClick={() => setCols(Math.max(1, cols - 1))}>-</button>
                  <input
                    type="number"
                    value={cols}
                    onChange={(e) => setCols(Math.max(1, Number(e.target.value)))}
                    min={1}
                  />
                  <button onClick={() => setCols(cols + 1)}>+</button>
                </div>
              </div>
            </div>
            {Array.from({ length: cols }, (_, i) => (
              <div key={i} className="header-cell">
                <div>Consumer {i + 1}</div>
                <input
                  type="number"
                  placeholder="Demand"
                  value={consumers[i] || ''}
                  min={1}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    if (value <= 0) return;
                    const newConsumers = [...consumers];
                    newConsumers[i] = Number(e.target.value);
                    setConsumers(newConsumers);
                  }}
                />
              </div>
            ))}
          </div>

          <div className="table-body">
            {Array.from({ length: rows }, (_, row) => (
              <div
                key={row}
                className="table-row"
                style={{ gridTemplateColumns: `150px repeat(${cols}, minmax(80px, 1fr))` }}
              >
                <div className="supplier-cell">
                  <div>Supplier {row + 1}</div>
                  <input
                    type="number"
                    placeholder="Supply"
                    value={suppliers[row] || ''}
                    min={1}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      if (value <= 0) return;
                      const newSuppliers = [...suppliers];
                      newSuppliers[row] = Number(e.target.value);
                      setSuppliers(newSuppliers);
                    }}
                  />
                </div>
                {Array.from({ length: cols }, (_, col) => (
                  <input
                    key={col}
                    type="number"
                    className="table-cell"
                    value={tableData[row]?.[col]?.value ?? ''}
                    min={0}
                    onChange={(e) => updateCell(row, col, e.target.value ? Number(e.target.value) : null)}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {capacityError && <div className="capacity-error">{capacityError}</div>}

      <div className="method-select">
        <label htmlFor="method">Method for Basic Plan:</label>
        <select id="method" value={method} onChange={(e) => setMethod(e.target.value as typeof method)}>
          <option value="northwest">Northwest Corner</option>
          <option value="min_cost">Minimum Cost</option>
          <option value="vogel">Vogel's</option>
        </select>
      </div>

      <div className="buttons-container">
        <button
          className="solve-button"
          onClick={() => solvePlan('basic')}
          disabled={isSolving || !!capacityError}
        >
          {isSolving ? 'Solving...' : 'Create Basic Plan'}
        </button>
        <button
          className="solve-button"
          onClick={() => solvePlan('optimal')}
          disabled={isSolving || !!capacityError}
        >
          {isSolving ? 'Solving...' : 'Create Optimal Plan'}
        </button>
      </div>

      {notification && (
        <div className={`notification ${isNotificationVisible ? 'slide-in' : 'slide-out'}`}>
          {notification}
        </div>
      )}

      {isModalOpen && solutionData && (
        <div className="modal">
          <div className="modal-content">
            <h2>{solutionData.is_optimal ? 'Optimal' : 'Basic'} Plan Solution</h2>
            <div className="solution-info">
              <p>Total Price: {solutionData.price}</p>
              <p>Is Optimal: {solutionData.is_optimal ? 'Yes' : 'No'}</p>
            </div>

            <div className="solution-table-container">
              <div className="solution-table-wrapper">
                <div
                  className="solution-table-header"
                  style={{ gridTemplateColumns: `150px repeat(${cols}, minmax(80px, 1fr))` }}
                >
                  <div className="corner-cell">Solution</div>
                  {Array.from({ length: cols }, (_, i) => (
                    <div key={i} className="header-cell">
                      <div>Consumer {i + 1}</div>
                      <div className="demand-value">{consumers[i] || 0}</div>
                    </div>
                  ))}
                </div>

                <div className="solution-table-body">
                  {getSolutionGrid().map((row, rowIndex) => (
                    <div
                      key={rowIndex}
                      className="solution-table-row"
                      style={{ gridTemplateColumns: `150px repeat(${cols}, minmax(80px, 1fr))` }}
                    >
                      <div className="supplier-cell">
                        <div>Supplier {rowIndex + 1}</div>
                        <div className="supply-value">{suppliers[rowIndex] || 0}</div>
                      </div>
                      {row.map((value, colIndex) => (
                        <div key={colIndex} className="solution-cell">{value}</div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="modal-buttons">
              <button onClick={() => setIsModalOpen(false)}>Close</button>
              <button onClick={handleSaveSolution}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransportSolver;
