import React, { useState, useEffect } from 'react';
import { 
    Paper, Group, Select, Button, Checkbox, Table, Text, 
    Card, Badge, Avatar, LoadingOverlay, ScrollArea, Box, 
    Modal, Tooltip 
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { 
    IconFileDownload, IconSearch, IconZoomIn, IconZoomOut, IconRotate, IconJson
} from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [workersList, setWorkersList] = useState([]); 
  const [reportData, setReportData] = useState(null); 
  const [previewImage, setPreviewImage] = useState(null); 
  const [zoomLevel, setZoomLevel] = useState(1);
  const [filters, setFilters] = useState({
    workerId: 'all',          
    dateRange: [null, null],  
    includeValid: true,       
    includeInvalid: true      
  });

  useEffect(() => {
    const fetchWorkers = async () => {
        try {
            const data = await workerApi.getAll();
            const list = Array.isArray(data) ? data : (data.workers || []);
            const selectOptions = list.map(w => ({ value: w.id.toString(), label: w.name }));
            setWorkersList([{ value: 'all', label: 'All Employees' }, ...selectOptions]);
        } catch (err) {
            console.error("Error loading employees:", err);
        }
    };
    fetchWorkers();
  }, []);

  useEffect(() => {
        handleGenerate();
    }, []);

  const handleGenerate = async () => {
    setLoading(true);
    try {
        const data = await workerApi.getReportData(filters);
        setReportData(data);
    } catch (err) {
        alert("Failed to generate report: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  const handleDownloadJson = () => {
    if (!reportData) return;

    // 1. Konwersja obiektu danych na tekst JSON (z wcięciami dla czytelności)
    const jsonString = JSON.stringify(reportData, null, 2);
    
    // 2. Tworzenie Bloba (wirtualnego pliku)
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    
    // 3. Pobieranie pliku (technika "niewidzialnego linku")
    const link = document.createElement('a');
    link.href = url;
    link.download = `Raport_Dane_${new Date().toISOString().slice(0,10)}.json`;
    
    document.body.appendChild(link);
    link.click();
    
    // 4. Sprzątanie
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    setLoading(true);
    try {
        const blob = await workerApi.downloadReportPdf(filters);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Entry_Report_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert("Error downloading PDF: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  const openPreview = (base64Image) => {
    if (!base64Image) return;
    setPreviewImage(base64Image);
    setZoomLevel(1);
  };

  const closePreview = () => {
    setPreviewImage(null);
  };

  const handleZoom = (delta) => {
    setZoomLevel(prev => Math.max(0.5, Math.min(prev + delta, 5)));
  };

  return (
    <Box>
      <Text size="xl" fw={700} mb="lg">Report Generator</Text>

      <Paper withBorder p="md" radius="md" mb="lg">
        <Group align="flex-end">
            <Select
                label="Employee"
                placeholder="Select..."
                data={workersList}
                value={filters.workerId}
                onChange={(val) => setFilters({...filters, workerId: val})}
                searchable
                style={{ flex: 1 }}
            />
            <DatePickerInput
                type="range"
                label="Time Period"
                placeholder="From - To"
                value={filters.dateRange}
                onChange={(val) => setFilters({...filters, dateRange: val})}
                style={{ flex: 1 }}
            />
        </Group>

        <Group mt="md" justify="space-between" align="center">
            <Group>
                <Text size="sm" fw={500}>Entry Status:</Text>
                <Checkbox label="Valid" checked={filters.includeValid} onChange={(e) => setFilters({...filters, includeValid: e.currentTarget.checked})} color="green" />
                <Checkbox label="Invalid" checked={filters.includeInvalid} onChange={(e) => setFilters({...filters, includeInvalid: e.currentTarget.checked})} color="red" />
            </Group>
            <Group>
                <Button leftSection={<IconSearch size={16}/>} onClick={handleGenerate} loading={loading}>Generate Preview</Button>
                <Button leftSection={<IconJson size={16}/>} variant="default" onClick={handleDownloadJson} disabled={!reportData}>Download JSON</Button>
                <Button leftSection={<IconFileDownload size={16}/>} variant="outline" color="red" onClick={handleDownloadPdf} loading={loading} disabled={!reportData}>Download PDF</Button>
            </Group>
        </Group>
      </Paper>

      <Card withBorder shadow="sm" radius="md" style={{ minHeight: 200, position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        
        <ScrollArea h={500}>
            <Table striped highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                  <Table.Tr>
                      <Table.Th>Date and Time</Table.Th>
                      <Table.Th>Employee</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Photo (Click)</Table.Th>
                      <Table.Th>System Message</Table.Th>
                  </Table.Tr>
              </Table.Thead>
                <Table.Tbody>
                {(() => {
                    let items = [];
                    if (!reportData) items = [];
                    else if (Array.isArray(reportData.data)) items = reportData.data;
                    else if (reportData.data && Array.isArray(reportData.data.items)) items = reportData.data.items;

                    if (items.length === 0) {
                        return (
                            <Table.Tr>
                                <Table.Td colSpan={5} style={{ textAlign: 'center', padding: 20 }}>
                                    <Text c="dimmed">No results for the given filters.</Text>
                                </Table.Td>
                            </Table.Tr>
                        );
                    }

                    return items.map((entry) => (
                        <Table.Tr key={entry.id}>
                            <Table.Td>{entry.date ? new Date(entry.date).toLocaleString('en-US') : '-'}</Table.Td>
                            <Table.Td><Text size="sm" fw={500}>{entry.worker_name || 'Unknown'}</Text></Table.Td>
                            <Table.Td>
                                {entry.code === 0 ? <Badge color="green">Valid</Badge> : <Badge color="red">Error ({entry.code})</Badge>}
                            </Table.Td>
                            <Table.Td>
                                {entry.face_image ? (
                                    <Tooltip label="Click to enlarge">
                                        <Avatar 
                                            src={`data:image/jpeg;base64,${entry.face_image}`} 
                                            size="lg" 
                                            radius="sm" 
                                            style={{ cursor: 'pointer', border: '1px solid #444' }}
                                            onClick={() => openPreview(entry.face_image)}
                                        />
                                    </Tooltip>
                                ) : (
                                    <Text c="dimmed" size="xs">None</Text>
                                )}
                            </Table.Td>
                            <Table.Td><Text size="sm" c={entry.code === 0 ? 'dimmed' : 'red'}>{entry.message}</Text></Table.Td>
                        </Table.Tr>
                    ));
                })()}
                </Table.Tbody>
            </Table>
        </ScrollArea>
      </Card>

      <Modal 
        opened={!!previewImage} 
        onClose={closePreview} 
        title="Camera Image Analysis" 
        size="xl" // Large modal
        centered
      >
        <Paper withBorder p="xs" mb="md">
            <Group justify="center">
                <Button variant="default" onClick={() => handleZoom(-0.5)} disabled={zoomLevel <= 0.5} leftSection={<IconZoomOut size={16}/>}>
                    Zoom Out
                </Button>
                <Text fw={700}>{Math.round(zoomLevel * 100)}%</Text>
                <Button variant="default" onClick={() => handleZoom(0.5)} disabled={zoomLevel >= 5} leftSection={<IconZoomIn size={16}/>}>
                    Zoom In
                </Button>
                <Button variant="subtle" color="blue" onClick={() => setZoomLevel(1)} leftSection={<IconRotate size={16}/>}>
                    Reset
                </Button>
            </Group>
        </Paper>

        <Box 
            style={{ 
                height: '60vh', 
                overflow: 'auto', 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                backgroundColor: '#1A1B1E',
                borderRadius: 8
            }}
        >
            {previewImage && (
                <img 
                    src={`data:image/jpeg;base64,${previewImage}`} 
                    alt="Analysis"
                    style={{ 
                        transform: `scale(${zoomLevel})`, 
                        transition: 'transform 0.2s ease-out',
                        maxWidth: '100%',
                        transformOrigin: 'center center' 
                    }} 
                />
            )}
        </Box>
      </Modal>

    </Box>
  );
}