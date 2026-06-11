import api from './api';

export const dataService = {
  getStatus: () => api.get('/data/status'),
  listDatasets: () => api.get('/data/datasets'),
  getDataset: (name: string) => api.get(`/data/dataset/${name}`),
  uploadCSV: (file: File, datasetName: string) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/data/upload?dataset_name=${datasetName}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadMultipleCSVs: (files: File[]) => {
    const form = new FormData();
    files.forEach((file) => {
      form.append('files', file);
    });
    return api.post('/data/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteDataset: (name: string) => api.delete(`/data/dataset/${name}`),
  mergeDatasets: (datasetNames: string[], mergedName: string) =>
    api.post('/data/merge', { dataset_names: datasetNames, merged_name: mergedName }),
  addManualRecord: (datasetName: string, record: any) =>
    api.post('/data/manual/record', { dataset_name: datasetName, record }),
  addManualBatch: (datasetName: string, records: any[]) =>
    api.post('/data/manual/batch', { dataset_name: datasetName, records }),
};
