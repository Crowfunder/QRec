import React, { useState, useEffect } from 'react';
import { Table, Group, Text, Button, Modal, TextInput, FileInput, Badge, Card } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconEdit, IconUpload, IconBan } from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';

export default function WorkersListPage() {
const [workers, setWorkers] = useState([]);
const [opened, setOpened] = useState(false);
const [loading, setLoading] = useState(false);
const [editingId, setEditingId] = useState(null);
const [formData, setFormData] = useState({ 
    name: '', 
    expiration_date: new Date(), 
    file: null 
  });

  useEffect(() => { loadWorkers(); }, []);

const loadWorkers = async () => {
    try {
        const data = await workerApi.getAll();
        if (Array.isArray(data)) {
            setWorkers(data);
        } else if (data && Array.isArray(data.workers)) {
            setWorkers(data.workers);
        } else {
            console.error("Unknown data format. Expected an array.", data);
            setWorkers([]); 
        }

    } catch (err) {
        console.error("API Error:", err);
    }
  };

  const handleEdit = (worker) => {
    setEditingId(worker.id);
    setFormData({
      name: worker.name,
      expiration_date: new Date(worker.expiration_date),
      file: null
    });
    setOpened(true);
  };

  const handleUpdate = async () => {
    setLoading(true);
    try {
        await workerApi.update(editingId, formData.name, formData.expiration_date, formData.file);
        setOpened(false);
        loadWorkers();
    } catch (err) {
        alert("Update failed: " + err.message);
    } finally {
        setLoading(false);
    }
  };

  const handleInvalidate = async (id) => {
    if(!window.confirm("Are you sure you want to INVALIDATE this pass immediately?")) return;
    try {
        await workerApi.invalidate(id);
        loadWorkers();
    } catch (err) {
        alert("Failed to invalidate pass");
    }
  };

  const isActive = (isoDate) => new Date(isoDate) > new Date();

  return (
    <div>
      <Text size="xl" fw={700} mb="lg">Workers & Passes Database</Text>

      <Card withBorder shadow="sm" radius="md">
        <Table striped highlightOnHover verticalSpacing="sm">
            <Table.Thead>
            <Table.Tr>
                <Table.Th>ID</Table.Th>
                <Table.Th>Worker Name</Table.Th>
                <Table.Th>Pass Expiration</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Actions</Table.Th>
            </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
            {workers.map((worker) => (
                <Table.Tr key={worker.id}>
                <Table.Td>{worker.id}</Table.Td>
                <Table.Td fw={500}>{worker.name}</Table.Td>
                <Table.Td>{new Date(worker.expiration_date).toLocaleDateString()}</Table.Td>
                <Table.Td>
                    {isActive(worker.expiration_date) 
                        ? <Badge color="green">ACTIVE</Badge> 
                        : <Badge color="gray">EXPIRED</Badge>}
                </Table.Td>
                <Table.Td>
                    <Group gap="xs">
                        <Button leftSection={<IconEdit size={16}/>} variant="light" size="xs" onClick={() => handleEdit(worker)}>
                            Edit
                        </Button>
                        {isActive(worker.expiration_date) && (
                            <Button leftSection={<IconBan size={16}/>} color="red" variant="subtle" size="xs" onClick={() => handleInvalidate(worker.id)}>
                                Invalidate
                            </Button>
                        )}
                    </Group>
                </Table.Td>
                </Table.Tr>
            ))}
            </Table.Tbody>
        </Table>
      </Card>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Edit Worker Details">
        <TextInput
            label="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            mb="sm"
        />
        <DatePickerInput
            label="Pass Expiration Date"
            value={formData.expiration_date}
            onChange={(date) => setFormData({...formData, expiration_date: date})}
            mb="sm"
        />
        <FileInput
            label="Update Photo (Optional)"
            placeholder="Choose new file..."
            leftSection={<IconUpload size={14} />}
            value={formData.file}
            onChange={(file) => setFormData({...formData, file: file})}
            mb="lg"
        />
        <Group justify="flex-end">
            <Button variant="default" onClick={() => setOpened(false)}>Cancel</Button>
            <Button onClick={handleUpdate} loading={loading}>Save Changes</Button>
        </Group>
      </Modal>
    </div>
  );
}