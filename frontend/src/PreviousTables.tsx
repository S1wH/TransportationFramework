import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ParticlesBackground from './ParticlesBackground';
import { FullTable } from './types';
import './App.css';

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

type TableData = {
  suppliers: number[];
  consumers: number[];
  price_matrix: number[][];
  restrictions: Record<string, any>;
  capacities: number[][];
  user_id: number;
};

interface SolutionData {
  table: TableData;
  solution: SolutionResponse;
}

const PreviousTables: React.FC<{ userId: string }> = ({ userId }) => {
  const navigate = useNavigate();
  const [tables, setTables] = useState<FullTable[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [solutionData, setSolutionData] = useState<SolutionData | null>(null);
  const [notification, setNotification] = useState<string | null>(null);
  const [isNotificationVisible, setIsNotificationVisible] = useState(false);

  useEffect(() => {
    const fetchTables = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/tables/?user_id=${userId}`);
        if (response.ok) {
          const data: FullTable[] = await response.json();
          setTables(data);
        } else {
          console.error('Failed to fetch tables:', response.statusText);
        }
      } catch (err) {
        console.error('Error fetching tables:', err);
      }
    };
    fetchTables();
  }, [userId]);

  useEffect(() => {
    if (notification) {
      setIsNotificationVisible(true);
      const timer = setTimeout(() => {
        setIsNotificationVisible(false);
      }, 2700);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const viewPlan = async (tableId: string, planType: 'basic' | 'optimal') => {
    try {
      const endpoint =
        planType === 'basic'
          ? `http://127.0.0.1:8000/tables/last_basic_plan/${tableId}/?user_id=${userId}`
          : `http://127.0.0.1:8000/tables/last_optimal_plan/${tableId}/?user_id=${userId}`;
      console.log(endpoint);
      const response = await fetch(endpoint);
      if (response.ok) {
        const data: SolutionData = await response.json();
        if (data === null) {
          setNotification(`No ${planType} plan found for table ${tableId}`);
          setTimeout(() => setNotification(null), 3000);
        } else {
          setSolutionData(data);
          setIsModalOpen(true);
          setNotification(null);
        }
      } else {
        throw new Error('Response not OK');
      }
    } catch (err) {
      console.error(`Failed to fetch ${planType} plan`, err);
      setNotification(`Error fetching ${planType} plan`);
      setTimeout(() => setNotification(null), 3000);
    }
  };

  const getSolutionGrid = (): (string | number)[][] => {
    if (!solutionData?.solution.roots || !solutionData?.table) {
      return Array(solutionData?.table.suppliers.length || 0).fill(
        Array(solutionData?.table.consumers.length || 0).fill(0)
      );
    }

    const grid = Array.from(
      { length: solutionData.table.suppliers.length },
      () => Array(solutionData.table.consumers.length).fill(0)
    );

    solutionData.solution.roots.forEach((root) => {
      const { supplier_id: supplierId, consumer_id: consumerId, amount, epsilon } = root;
      if (supplierId < grid.length && consumerId < grid[0].length) {
        grid[supplierId][consumerId] = epsilon
          ? `${amount || ''}${epsilon > 0 ? '+' : '-'}${Math.abs(epsilon)}ε`
          : amount;
      }
    });
    return grid;
  };

  return (
    <div className="app dark-theme">
      <ParticlesBackground />
      <div className="previous-tables">
        <h2>Previous Tables</h2>
        <button onClick={() => navigate('/')}>Back to Main Page</button>
        <ul>
          {tables.map((table, index) => (
            <li key={index} className="table-item">
              <span className="table-counter">{index + 1}.</span>
              <span className="table-name">{table.name}</span>
              <button onClick={() => viewPlan(table.id.toString(), 'basic')}>
                View Basic Plan
              </button>
              <button onClick={() => viewPlan(table.id.toString(), 'optimal')}>
                View Optimal Plan
              </button>
              <button onClick={() => navigate('/', { state: { tableData: table } })}>
                Load Table
              </button>
            </li>
          ))}
        </ul>
      </div>

      {notification && (
        <div className={`notification ${isNotificationVisible ? 'slide-in' : 'slide-out'}`}>
          {notification}
        </div>
      )}

      {isModalOpen && solutionData && (
        <div className="modal">
          <div className="modal-content">
            <h2>{solutionData.solution.is_optimal ? 'Optimal' : 'Basic'} Plan Solution</h2>
            <div className="solution-info">
              <p>Total Price: {solutionData.solution.price}</p>
              <p>Is Optimal: {solutionData.solution.is_optimal ? 'Yes' : 'No'}</p>
            </div>

            <div className="solution-table-container">
              <div className="solution-table-wrapper">
                <div
                  className="solution-table-header"
                  style={{
                    gridTemplateColumns: `150px repeat(${solutionData.table.consumers.length}, minmax(80px, 1fr))`,
                  }}
                >
                  <div className="corner-cell">Solution</div>
                  {solutionData.table.consumers.map((demand, i) => (
                    <div key={i} className="header-cell">
                      <div>Consumer {i + 1}</div>
                      <div className="demand-value">{demand}</div>
                    </div>
                  ))}
                </div>

                <div className="solution-table-body">
                  {getSolutionGrid().map((row, rowIndex) => (
                    <div
                      key={rowIndex}
                      className="solution-table-row"
                      style={{
                        gridTemplateColumns: `150px repeat(${solutionData.table.consumers.length}, minmax(80px, 1fr))`,
                      }}
                    >
                      <div className="supplier-cell">
                        <div>Supplier {rowIndex + 1}</div>
                        <div className="supply-value">{solutionData.table.suppliers[rowIndex]}</div>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviousTables;
