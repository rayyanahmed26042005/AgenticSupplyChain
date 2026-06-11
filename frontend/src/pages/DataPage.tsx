import { useState, useEffect } from 'react';
import { dataService } from '../services/dataService';
import { simulationService } from '../services/simulationService';
import { Upload, Database, FileText, Table, Trash2, Plus, RefreshCw, FileSpreadsheet } from 'lucide-react';
import { useSimulationStore } from '../store/simulationStore';

export default function DataPage() {
  const [datasets, setDatasets] = useState<Record<string, any>>({});
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');

  // Row creation state
  const [targetDataset, setTargetDataset] = useState('');
  const [newDatasetName, setNewDatasetName] = useState('');
  const [rowData, setRowData] = useState({
    demand: 1000,
    inventory: 500,
    defect_rate: 0.02,
    lead_time: 10,
    cost: 50.0,
    revenue: 100.0,
  });
  const [submittingRow, setSubmittingRow] = useState(false);
  const [rowMsg, setRowMsg] = useState('');

  // Merging state
  const [selectedForMerge, setSelectedForMerge] = useState<string[]>([]);
  const [mergedDatasetName, setMergedDatasetName] = useState('');
  const [merging, setMerging] = useState(false);
  const [mergeMsg, setMergeMsg] = useState('');

  const handleToggleMergeSelection = (name: string) => {
    setSelectedForMerge((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  const handleMergeDatasets = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedForMerge.length < 2) {
      setMergeMsg('❌ Please select at least 2 datasets to merge.');
      return;
    }
    const name = mergedDatasetName.trim();
    if (!name) {
      setMergeMsg('❌ Please specify a merged dataset name.');
      return;
    }

    setMerging(true);
    setMergeMsg('');
    try {
      const res: any = await dataService.mergeDatasets(selectedForMerge, name);
      setMergeMsg(`✅ Successfully merged datasets into "${name}"!`);
      setSelectedForMerge([]);
      setMergedDatasetName('');
      await fetchDatasets();

      if (res.data && res.data.metrics) {
        useSimulationStore.getState().setResult(res.data);
      } else {
        const simRes: any = await simulationService.getLatest();
        if (simRes.data) {
          useSimulationStore.getState().setResult(simRes.data);
        }
      }
    } catch (err: any) {
      setMergeMsg(`❌ Merge failed: ${err.response?.data?.detail || err.message || 'Unknown error'}`);
    } finally {
      setMerging(false);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res: any = await dataService.listDatasets();
      setDatasets(res.data || {});
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    setUploadMsg('');
    try {
      const fileList = Array.from(files);
      let res: any;
      if (fileList.length === 1) {
        const file = fileList[0];
        const name = file.name.replace('.csv', '');
        res = await dataService.uploadCSV(file, name);
      } else {
        res = await dataService.uploadMultipleCSVs(fileList);
      }

      if (res.data && res.data.metrics) {
        useSimulationStore.getState().setResult(res.data);
        setUploadMsg(`✅ Uploaded ${fileList.length} file(s) successfully. Dashboard updated!`);
      } else {
        setUploadMsg(`✅ Uploaded ${fileList.length} file(s) successfully.`);
      }
      await fetchDatasets();
    } catch (err: any) {
      setUploadMsg(`❌ Upload failed: ${err.response?.data?.detail || err.detail || err.message || 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDataset = async (name: string) => {
    if (!window.confirm(`Are you sure you want to delete dataset "${name}"? This will also remove it from MongoDB Atlas.`)) {
      return;
    }
    try {
      await dataService.deleteDataset(name);
      setUploadMsg(`✅ Dataset "${name}" deleted successfully.`);
      await fetchDatasets();

      // Refresh simulation dashboard store
      try {
        const simRes: any = await simulationService.getLatest();
        if (simRes.data) {
          useSimulationStore.getState().setResult(simRes.data);
        } else {
          useSimulationStore.getState().reset();
        }
      } catch (simErr) {
        console.error('Failed to update active simulation store after deletion:', simErr);
      }
    } catch (err: any) {
      setUploadMsg(`❌ Failed to delete dataset: ${err.response?.data?.detail || err.message || 'Unknown error'}`);
    }
  };

  const handleAddRow = async (e: React.FormEvent) => {
    e.preventDefault();
    const datasetName = targetDataset === 'new' ? newDatasetName.trim() : targetDataset;
    if (!datasetName) {
      setRowMsg('❌ Please specify a dataset name');
      return;
    }

    setSubmittingRow(true);
    setRowMsg('');
    try {
      const record = {
        products_sold: Number(rowData.demand),
        inventory: Number(rowData.inventory),
        defect_rate: Number(rowData.defect_rate),
        lead_time: Number(rowData.lead_time),
        cost: Number(rowData.cost),
        revenue: Number(rowData.revenue),
      };

      const res: any = await dataService.addManualRecord(datasetName, record);
      setRowMsg(`✅ Row added to dataset "${datasetName}" successfully!`);
      
      if (targetDataset === 'new') {
        setTargetDataset(datasetName);
        setNewDatasetName('');
      }
      await fetchDatasets();

      // Refresh simulation dashboard store if the modified dataset was compiled
      try {
        const simRes: any = await simulationService.getLatest();
        if (simRes.data) {
          useSimulationStore.getState().setResult(simRes.data);
        }
      } catch (simErr) {
        console.error('Failed to update active simulation store after row insertion:', simErr);
      }
    } catch (err: any) {
      setRowMsg(`❌ Failed to add row: ${err.response?.data?.detail || err.message || 'Unknown error'}`);
    } finally {
      setSubmittingRow(false);
    }
  };

  return (
    <div className="page-container animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Data Management</h1>
        <p className="page-description">Upload CSV files, manage datasets, add records, and configure Atlas DB data sources</p>
      </div>

      {/* Upload Section */}
      <div className="glass-card" style={{ marginBottom: 24 }}>
        <div className="section-header">
          <span className="section-title">📤 Upload Data</span>
        </div>
        <div style={{
          border: '2px dashed var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: '48px 32px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all var(--transition-fast)',
          position: 'relative',
        }}>
          <Upload size={48} style={{ color: 'var(--accent-primary)', opacity: 0.5, marginBottom: 16 }} />
          <p style={{ fontWeight: 600, marginBottom: 4 }}>Drag & drop or click to upload</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>CSV files up to 500MB (Select multiple files to upload at once)</p>
          <input
            type="file"
            accept=".csv"
            multiple
            onChange={handleUpload}
            disabled={uploading}
            style={{
              position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer',
            }}
          />
        </div>
        {uploadMsg && (
          <p style={{
            marginTop: 12, fontSize: '0.85rem', fontWeight: 500,
            color: uploadMsg.includes('success') ? 'var(--success)' : 'var(--danger)',
          }}>
            {uploadMsg}
          </p>
        )}
      </div>

      {/* Add Row Section */}
      <div className="glass-card" style={{ marginBottom: 24 }}>
        <div className="section-header">
          <span className="section-title">➕ Add Row to Dataset</span>
        </div>
        <form onSubmit={handleAddRow} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="grid-2">
            <div>
              <label className="label">Target Dataset</label>
              <select
                className="input"
                value={targetDataset}
                onChange={(e) => setTargetDataset(e.target.value)}
                required
              >
                <option value="">-- Select Dataset --</option>
                <option value="new">Create New Manual Dataset</option>
                {Object.keys(datasets).map((name) => (
                  <option key={name} value={name}>
                    {name} ({datasets[name].source})
                  </option>
                ))}
              </select>
            </div>
            
            {targetDataset === 'new' && (
              <div>
                <label className="label">New Dataset Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. manual_inventory_data"
                  value={newDatasetName}
                  onChange={(e) => setNewDatasetName(e.target.value)}
                  required
                />
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            <div>
              <label className="label">Demand (units)</label>
              <input
                type="number"
                className="input"
                value={rowData.demand}
                onChange={(e) => setRowData({ ...rowData, demand: parseFloat(e.target.value) || 0 })}
                min="0"
                required
              />
            </div>
            <div>
              <label className="label">Inventory (units)</label>
              <input
                type="number"
                className="input"
                value={rowData.inventory}
                onChange={(e) => setRowData({ ...rowData, inventory: parseFloat(e.target.value) || 0 })}
                min="0"
                required
              />
            </div>
            <div>
              <label className="label">Defect Rate (%)</label>
              <input
                type="number"
                step="0.01"
                className="input"
                value={rowData.defect_rate * 100}
                onChange={(e) => setRowData({ ...rowData, defect_rate: (parseFloat(e.target.value) || 0) / 100 })}
                min="0"
                max="100"
                required
              />
            </div>
            <div>
              <label className="label">Lead Time (days)</label>
              <input
                type="number"
                className="input"
                value={rowData.lead_time}
                onChange={(e) => setRowData({ ...rowData, lead_time: parseInt(e.target.value) || 0 })}
                min="0"
                required
              />
            </div>
            <div>
              <label className="label">Cost ($)</label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={rowData.cost}
                onChange={(e) => setRowData({ ...rowData, cost: parseFloat(e.target.value) || 0 })}
                min="0"
                required
              />
            </div>
            <div>
              <label className="label">Revenue ($)</label>
              <input
                type="number"
                step="0.1"
                className="input"
                value={rowData.revenue}
                onChange={(e) => setRowData({ ...rowData, revenue: parseFloat(e.target.value) || 0 })}
                min="0"
                required
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submittingRow}
            >
              <Plus size={16} />
              {submittingRow ? 'Adding Row...' : 'Add Row'}
            </button>
          </div>

          {rowMsg && (
            <p style={{
              fontSize: '0.85rem', fontWeight: 500,
              color: rowMsg.includes('success') ? 'var(--success)' : 'var(--danger)',
            }}>
              {rowMsg}
            </p>
          )}
        </form>
      </div>

      {/* Merge Datasets Section */}
      {Object.keys(datasets).length >= 2 && (
        <div className="glass-card" style={{ marginBottom: 24 }}>
          <div className="section-header">
            <span className="section-title">🔗 Chronological Dataset Merge</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
            Select multiple datasets to merge them sequentially (e.g. Day 0-14 of Dataset A + Day 15-29 of Dataset B). The AI Agents will analyze the combined historical timeline.
          </p>
          <form onSubmit={handleMergeDatasets}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
              <label className="label">Select Datasets to Merge (in sequential order):</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12 }}>
                {Object.entries(datasets).map(([name, info]: any) => (
                  <label
                    key={name}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 14px',
                      background: selectedForMerge.includes(name) ? 'var(--bg-hover)' : 'var(--bg-tertiary)',
                      border: `1px solid ${selectedForMerge.includes(name) ? 'var(--accent-primary)' : 'var(--border)'}`,
                      borderRadius: 'var(--radius-md)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedForMerge.includes(name)}
                      onChange={() => handleToggleMergeSelection(name)}
                      style={{ cursor: 'pointer' }}
                    />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{name}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {info.rows} rows · {info.source}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {selectedForMerge.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 16, background: 'var(--bg-tertiary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Sequence:</span>
                {selectedForMerge.map((name, index) => (
                  <span key={name} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ background: 'var(--accent-primary)', color: 'white', borderRadius: '50%', width: 16, height: 16, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 'bold' }}>{index + 1}</span>
                    <strong style={{ color: 'var(--text-primary)' }}>{name}</strong>
                    {index < selectedForMerge.length - 1 && <span style={{ color: 'var(--text-muted)' }}>&rarr;</span>}
                  </span>
                ))}
              </div>
            )}

            <div className="grid-2" style={{ alignItems: 'flex-end' }}>
              <div>
                <label className="label">Merged Dataset Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. combined_jan_feb"
                  value={mergedDatasetName}
                  onChange={(e) => setMergedDatasetName(e.target.value)}
                  required
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={merging || selectedForMerge.length < 2}
                  style={{ width: '100%' }}
                >
                  <FileSpreadsheet size={16} />
                  {merging ? 'Merging Datasets...' : 'Merge Datasets'}
                </button>
              </div>
            </div>

            {mergeMsg && (
              <p style={{
                marginTop: 12, fontSize: '0.85rem', fontWeight: 500,
                color: mergeMsg.includes('success') ? 'var(--success)' : 'var(--danger)',
              }}>
                {mergeMsg}
              </p>
            )}
          </form>
        </div>
      )}

      {/* Datasets */}
      <div className="glass-card">
        <div className="section-header">
          <span className="section-title">📊 Loaded Datasets</span>
          <button className="btn btn-secondary btn-sm" onClick={fetchDatasets}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        {Object.keys(datasets).length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {Object.entries(datasets).map(([name, info]: any) => (
              <div key={name} style={{
                padding: '14px 16px', background: 'var(--bg-tertiary)',
                borderRadius: 'var(--radius-md)', display: 'flex',
                justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Table size={20} style={{ color: 'var(--accent-primary)' }} />
                  <div>
                    <div style={{ fontWeight: 600 }}>{name}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {info.rows} rows · {info.source} · {new Date(info.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span className="badge badge-success">Loaded</span>
                  <button
                    onClick={() => handleDeleteDataset(name)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--danger)',
                      cursor: 'pointer',
                      padding: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      borderRadius: 'var(--radius-sm)',
                      transition: 'background var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'var(--danger-bg)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    title="Delete dataset"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
            <FileText size={40} style={{ opacity: 0.3, marginBottom: 12 }} />
            <p>No datasets loaded. Upload CSV files or add a new record.</p>
          </div>
        )}
      </div>
    </div>
  );
}
