import React, { useState } from 'react';
import { MantineProvider } from '@mantine/core';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';

import EntryTerminal from './pages/EntryTerminal';
import AdminLayout from './pages/admin/AdminLayout';
import WorkersListPage from './pages/admin/WorkersListPage'; 
import AddWorkerPage from './pages/admin/AddWorkerPage'; 
import ReportsPage from './pages/admin/ReportsPage';
import HeadManager from './components/HeadManager';

function App() {
  return (
    <MantineProvider defaultColorScheme="dark">
      <BrowserRouter>
        <HeadManager/>
      
        <Routes>
            <Route path="/" element={<EntryTerminal />} />
            <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<Navigate to="/admin/workers" replace />} />
                
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