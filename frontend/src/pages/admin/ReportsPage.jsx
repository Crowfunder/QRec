import React, { useState, useEffect } from 'react';
import { 
    Paper, Group, Select, Button, Checkbox, Table, Text, 
    Card, Badge, Avatar, LoadingOverlay, ScrollArea, Box, 
    Modal, ActionIcon, Tooltip, Center 
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { 
    IconFileDownload, IconSearch, IconZoomIn, IconZoomOut, IconRotate 
} from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [workersList, setWorkersList] = useState([]); 
  const [reportData, setReportData] = useState(null); 

  // 👇 NOWE: Stany do obsługi podglądu zdjęcia
  const [previewImage, setPreviewImage] = useState(null); // Base64 otwartego zdjęcia
  const [zoomLevel, setZoomLevel] = useState(1);          // Poziom przybliżenia (1 = 100%)

  // Stan Filtrów
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
            setWorkersList([{ value: 'all', label: 'Wszyscy Pracownicy' }, ...selectOptions]);
        } catch (err) {
            console.error("Błąd ładowania pracowników:", err);
        }
    };
    fetchWorkers();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    try {
        const data = await workerApi.getReportData(filters);
        setReportData(data);
    } catch (err) {
        alert("Nie udało się wygenerować raportu: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    setLoading(true);
    try {
        const blob = await workerApi.downloadReportPdf(filters);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Raport_Wejsc_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert("Błąd pobierania PDF: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  // 👇 NOWE: Funkcje obsługi podglądu
  const openPreview = (base64Image) => {
    if (!base64Image) return;
    setPreviewImage(base64Image);
    setZoomLevel(1); // Reset zoomu przy otwarciu
  };

  const closePreview = () => {
    setPreviewImage(null);
  };

  const handleZoom = (delta) => {
    setZoomLevel(prev => Math.max(0.5, Math.min(prev + delta, 5))); // Max zoom 5x, min 0.5x
  };

  return (
    <Box>
      <Text size="xl" fw={700} mb="lg">Generator Raportów</Text>

      {/* SEKCJA FILTRÓW */}
      <Paper withBorder p="md" radius="md" mb="lg">
        <Group align="flex-end">
            <Select
                label="Pracownik"
                placeholder="Wybierz..."
                data={workersList}
                value={filters.workerId}
                onChange={(val) => setFilters({...filters, workerId: val})}
                searchable
                style={{ flex: 1 }}
            />
            <DatePickerInput
                type="range"
                label="Okres czasu"
                placeholder="Od - Do"
                value={filters.dateRange}
                onChange={(val) => setFilters({...filters, dateRange: val})}
                style={{ flex: 1 }}
            />
        </Group>

        <Group mt="md" justify="space-between" align="center">
            <Group>
                <Text size="sm" fw={500}>Stan wejścia:</Text>
                <Checkbox label="Poprawne" checked={filters.includeValid} onChange={(e) => setFilters({...filters, includeValid: e.currentTarget.checked})} color="green" />
                <Checkbox label="Niepoprawne" checked={filters.includeInvalid} onChange={(e) => setFilters({...filters, includeInvalid: e.currentTarget.checked})} color="red" />
            </Group>
            <Group>
                <Button leftSection={<IconSearch size={16}/>} onClick={handleGenerate} loading={loading}>Generuj Podgląd</Button>
                <Button leftSection={<IconFileDownload size={16}/>} variant="outline" color="red" onClick={handleDownloadPdf} loading={loading} disabled={!reportData}>Pobierz PDF</Button>
            </Group>
        </Group>
      </Paper>

      {/* SEKCJA WYNIKÓW */}
      <Card withBorder shadow="sm" radius="md" style={{ minHeight: 200, position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        
        <ScrollArea h={500}>
            <Table striped highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                  <Table.Tr>
                      <Table.Th>Data i Czas</Table.Th>
                      <Table.Th>Pracownik</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Zdjęcie (Kliknij)</Table.Th>
                      <Table.Th>Wiadomość Systemowa</Table.Th>
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
                                    <Text c="dimmed">Brak wyników dla podanych filtrów.</Text>
                                </Table.Td>
                            </Table.Tr>
                        );
                    }

                    return items.map((entry) => (
                        <Table.Tr key={entry.id}>
                            <Table.Td>{entry.date ? new Date(entry.date).toLocaleString('pl-PL') : '-'}</Table.Td>
                            <Table.Td><Text size="sm" fw={500}>{entry.worker_name || 'Nieznany'}</Text></Table.Td>
                            <Table.Td>
                                {entry.code === 0 ? <Badge color="green">Poprawne</Badge> : <Badge color="red">Błąd ({entry.code})</Badge>}
                            </Table.Td>
                            <Table.Td>
                                {entry.face_image ? (
                                    <Tooltip label="Kliknij, aby powiększyć">
                                        <Avatar 
                                            src={`data:image/jpeg;base64,${entry.face_image}`} 
                                            size="lg" 
                                            radius="sm" 
                                            // 👇 NOWE: Kliknięcie otwiera podgląd
                                            style={{ cursor: 'pointer', border: '1px solid #444' }}
                                            onClick={() => openPreview(entry.face_image)}
                                        />
                                    </Tooltip>
                                ) : (
                                    <Text c="dimmed" size="xs">Brak</Text>
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

      {/* 👇 NOWE: MODAL Z PODGLĄDEM ZDJĘCIA */}
      <Modal 
        opened={!!previewImage} 
        onClose={closePreview} 
        title="Analiza Obrazu z Kamery" 
        size="xl" // Duży modal
        centered
      >
        <Paper withBorder p="xs" mb="md">
            <Group justify="center">
                <Button variant="default" onClick={() => handleZoom(-0.5)} disabled={zoomLevel <= 0.5} leftSection={<IconZoomOut size={16}/>}>
                    Oddal
                </Button>
                <Text fw={700}>{Math.round(zoomLevel * 100)}%</Text>
                <Button variant="default" onClick={() => handleZoom(0.5)} disabled={zoomLevel >= 5} leftSection={<IconZoomIn size={16}/>}>
                    Przybliż
                </Button>
                <Button variant="subtle" color="blue" onClick={() => setZoomLevel(1)} leftSection={<IconRotate size={16}/>}>
                    Reset
                </Button>
            </Group>
        </Paper>

        {/* Kontener ze scrollem dla powiększonego zdjęcia */}
        <Box 
            style={{ 
                height: '60vh', 
                overflow: 'auto', 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center',
                backgroundColor: '#1A1B1E', // Ciemne tło dla lepszego kontrastu
                borderRadius: 8
            }}
        >
            {previewImage && (
                <img 
                    src={`data:image/jpeg;base64,${previewImage}`} 
                    alt="Analiza"
                    style={{ 
                        transform: `scale(${zoomLevel})`, 
                        transition: 'transform 0.2s ease-out',
                        maxWidth: '100%',
                        // Kluczowe: jeśli zoom > 1, pozwalamy obrazowi wyjść poza obrys, aby scroll działał
                        transformOrigin: 'center center' 
                    }} 
                />
            )}
        </Box>
      </Modal>

    </Box>
  );
}