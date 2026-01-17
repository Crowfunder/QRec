import React, { useState, useEffect } from 'react';
import { 
    Paper, Group, Select, Button, Checkbox, Table, Text, 
    Card, Badge, Avatar, LoadingOverlay, ScrollArea, Box 
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconFileDownload, IconSearch, IconFilter } from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [workersList, setWorkersList] = useState([]);
  const [reportData, setReportData] = useState(null);

  // Filter State
  const [filters, setFilters] = useState({
    workerId: 'all',          // 'all' or worker ID
    dateRange: [null, null],  // [Start, End]
    includeValid: true,       // Checked by default
    includeInvalid: true      // Checked by default
  });

  // 1. Load worker list into filter on start
  useEffect(() => {
    const fetchWorkers = async () => {
        try {
            const data = await workerApi.getAll();
            const list = Array.isArray(data) ? data : (data.workers || []);

            const selectOptions = list.map(w => ({ value: w.id.toString(), label: w.name }));
            setWorkersList([{ value: 'all', label: 'All Workers' }, ...selectOptions]);
        } catch (err) {
            console.error("Error loading workers:", err);
        }
    };
    fetchWorkers();
  }, []);

  // 2. Generate Report (Table Preview)
  const handleGenerate = async () => {
    setLoading(true);
    try {
        const data = await workerApi.getReportData(filters);
        console.log("REPORT FROM BACKEND:", data);
        setReportData(data);
    } catch (err) {
        alert("Failed to generate report: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  // 3. Download PDF
  const handleDownloadPdf = async () => {
    setLoading(true);
    try {
        const blob = await workerApi.downloadReportPdf(filters);
        // Create temporary download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Translated filename to English
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

  return (
    <Box>
      <Text size="xl" fw={700} mb="lg">Report Generator</Text>

      {/* FILTER SECTION */}
      <Paper withBorder p="md" radius="md" mb="lg">
        <Group align="flex-end">
            <Select
                label="Worker"
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
                <Checkbox 
                    label="Valid (Success)" 
                    checked={filters.includeValid}
                    onChange={(e) => setFilters({...filters, includeValid: e.currentTarget.checked})}
                    color="green"
                />
                <Checkbox 
                    label="Invalid (Errors)" 
                    checked={filters.includeInvalid}
                    onChange={(e) => setFilters({...filters, includeInvalid: e.currentTarget.checked})}
                    color="red"
                />
            </Group>

            <Group>
                <Button 
                    leftSection={<IconSearch size={16}/>} 
                    onClick={handleGenerate}
                    loading={loading}
                >
                    Generate Preview
                </Button>
                <Button 
                    leftSection={<IconFileDownload size={16}/>} 
                    variant="outline" 
                    color="red" 
                    onClick={handleDownloadPdf}
                    loading={loading}
                    disabled={!reportData} // Enabled only after generating preview
                >
                    Download PDF
                </Button>
            </Group>
        </Group>
      </Paper>

      {/* RESULTS SECTION */}
      <Card withBorder shadow="sm" radius="md" style={{ minHeight: 200, position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        
        {!reportData ? (
            <Text c="dimmed" ta="center" py="xl">Set filters and click "Generate Preview" to view data.</Text>
        ) : (
            <>
                <Group justify="space-between" mb="md">
                    <Text fw={700}>Entries found: {reportData.count}</Text>
                </Group>

                <ScrollArea h={500}>
                    <Table striped highlightOnHover verticalSpacing="sm">
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Date & Time</Table.Th>
                                <Table.Th>Worker</Table.Th>
                                <Table.Th>Status</Table.Th>
                                <Table.Th>Camera Image</Table.Th>
                                <Table.Th>System Message</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        
                        <Table.Tbody>
                            {(() => {
                                // Smart array retrieval logic
                                let items = [];

                                if (!reportData) {
                                    items = [];
                                } 
                                // 1. Check if `data` is directly an array
                                else if (Array.isArray(reportData.data)) {
                                    items = reportData.data;
                                } 
                                // 2. Check old format (data.items)
                                else if (reportData.data && Array.isArray(reportData.data.items)) {
                                    items = reportData.data.items;
                                }

                                // If still empty after check
                                if (items.length === 0) {
                                    return (
                                        <Table.Tr>
                                            <Table.Td colSpan={5} style={{ textAlign: 'center', padding: 20 }}>
                                                <Text c="dimmed">No results for selected filters.</Text>
                                            </Table.Td>
                                        </Table.Tr>
                                    );
                                }

                                // Map results
                                return items.map((entry) => (
                                    <Table.Tr key={entry.id}>
                                        <Table.Td>
                                            {/* Changed to en-US for English formatting */}
                                            {entry.date ? new Date(entry.date).toLocaleString('en-US') : '-'}
                                        </Table.Td>
                                        <Table.Td>
                                            <Group gap="xs">
                                                <Text size="sm" fw={500}>{entry.worker_name || 'Unknown'}</Text>
                                            </Group>
                                        </Table.Td>
                                        <Table.Td>
                                            {/* Error code handling: 0 = OK, other = Error */}
                                            {entry.code === 0 
                                                ? <Badge color="green">Valid</Badge> 
                                                : <Badge color="red">Error ({entry.code})</Badge>
                                            }
                                        </Table.Td>
                                        <Table.Td>
                                            {entry.face_image ? (
                                                <Avatar 
                                                    src={`data:image/jpeg;base64,${entry.face_image}`} 
                                                    size="lg" 
                                                    radius="sm" 
                                                />
                                            ) : (
                                                <Text c="dimmed" size="xs">None</Text>
                                            )}
                                        </Table.Td>
                                        <Table.Td>
                                            <Text size="sm" c={entry.code === 0 ? 'dimmed' : 'red'}>
                                                {entry.message}
                                            </Text>
                                        </Table.Td>
                                    </Table.Tr>
                                ));
                            })()}
                        </Table.Tbody>
                    </Table>
                </ScrollArea>
            </>
        )}
      </Card>
    </Box>
  );
}