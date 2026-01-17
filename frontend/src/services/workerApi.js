const API_BASE = '/api/workers';
const REPORT_BASE = '/api/raport';

const formatDate = (date) => {
    if (!date) return '';
    
    if (date instanceof Date) {
        return date.toISOString();
    }
    
    return new Date(date).toISOString();
};

export const workerApi = {
    // GET /api/workers
    getAll: async () => {
        const res = await fetch(API_BASE);
        if (!res.ok) throw new Error('Failed to fetch workers');
        return res.json();
    },

    // POST /api/workers
    create: async (name, expirationDate, file) => {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('expiration_date', formatDate(expirationDate));
        formData.append('file', file); 

        const res = await fetch(API_BASE, {
            method: 'POST',
            body: formData, 
        });
        
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || 'Failed to create worker');
        }
        return res.json();
    },

    // PUT /api/workers/<id>
    update: async (id, name, expirationDate, file) => {
        const formData = new FormData();
        if (name) formData.append('name', name);
        if (expirationDate) formData.append('expiration_date', formatDate(expirationDate));
        if (file) formData.append('file', file);

        const res = await fetch(`${API_BASE}/${id}`, {
            method: 'PUT',
            body: formData,
        });

        if (!res.ok) throw new Error('Failed to update worker');
        return res.json();
    },

    // PUT /api/workers/invalidate/<id>
    invalidate: async (id) => {
        const res = await fetch(`${API_BASE}/invalidate/${id}`, {
            method: 'PUT'
        });
        if (!res.ok) throw new Error('Failed to invalidate worker');
        return res.json();
    },

    getEntryPass: async (id) => {
        const res = await fetch(`${API_BASE}/entrypass/${id}`);
        if (!res.ok) throw new Error('Failed to fetch entry pass');
        return res.blob();
    },

    getReportData: async (filters) => {
        const params = new URLSearchParams();

        if (filters.workerId && filters.workerId !== 'all') {
            params.append('pracownik_id', filters.workerId);
        }
        if (filters.dateRange && filters.dateRange[0]) {
            params.append('date_from', formatDate(filters.dateRange[0]));
        }
        if (filters.dateRange && filters.dateRange[1]) {
            params.append('date_to', formatDate(filters.dateRange[1]));
        }
        if (filters.includeValid) params.append('wejscia_poprawne', 'true');
        if (filters.includeInvalid) params.append('wejscia_niepoprawne', 'true');

        const res = await fetch(`${REPORT_BASE}?${params.toString()}`);
        if (!res.ok) throw new Error('Błąd pobierania raportu');
        return res.json();
    },

    downloadReportPdf: async (filters) => {
        const params = new URLSearchParams();

        if (filters.workerId && filters.workerId !== 'all') {
            params.append('pracownik_id', filters.workerId);
        }
        if (filters.dateRange && filters.dateRange[0]) {
            params.append('date_from', formatDate(filters.dateRange[0]));
        }
        if (filters.dateRange && filters.dateRange[1]) {
            params.append('date_to', formatDate(filters.dateRange[1]));
        }
        if (filters.includeValid) params.append('wejscia_poprawne', 'true');
        if (filters.includeInvalid) params.append('wejscia_niepoprawne', 'true');

        const res = await fetch(`${REPORT_BASE}/pdf?${params.toString()}`);
        if (!res.ok) throw new Error('Błąd generowania PDF');
        return res.blob();
    }
};