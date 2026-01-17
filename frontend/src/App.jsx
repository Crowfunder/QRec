import React from 'react';
import { MantineProvider } from '@mantine/core';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// 1. CSS Imports (Crucial for Mantine v7)
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';

// 2. Component Imports
import EntryTerminal from './pages/EntryTerminal';
import AdminLayout from './pages/admin/AdminLayout';
import WorkersListPage from './pages/admin/WorkersListPage'; // The new list view
import AddWorkerPage from './pages/admin/AddWorkerPage';     // The new create view
import ReportsPage from './pages/admin/ReportsPage';         // The new placeholder

function App() {
  return (
    <MantineProvider defaultColorScheme="dark">
      <BrowserRouter>
        <Routes>
            {/* PUBLIC TERMINAL (Home) */}
            <Route path="/" element={<EntryTerminal />} />
            
            {/* ADMIN PANEL */}
            <Route path="/admin" element={<AdminLayout />}>
                {/* Redirect /admin -> /admin/workers automatically */}
                <Route index element={<Navigate to="/admin/workers" replace />} />
                
                {/* Module Routes */}
                <Route path="workers" element={<WorkersListPage />} />
                <Route path="add-worker" element={<AddWorkerPage />} />
                <Route path="reports" element={<ReportsPage />} />
            </Route>
        </Routes>
      </BrowserRouter>
    </MantineProvider>
  );
}

export default App;