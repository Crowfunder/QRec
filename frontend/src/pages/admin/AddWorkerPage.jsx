import React, { useState } from 'react';
import { TextInput, FileInput, Button, Paper, Text, Notification } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconUpload, IconCheck, IconX } from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';
import { useNavigate } from 'react-router-dom';

export default function AddWorkerPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        expiration_date: new Date(),
        file: null
    });
    const [notification, setNotification] = useState(null);

    const handleSubmit = async () => {
        if (!formData.name || !formData.file) {
            setNotification({ color: 'red', message: 'Name and Photo are required!' });
            return;
        }

        setLoading(true);
        try {
            await workerApi.create(formData.name, formData.expiration_date, formData.file);
            // Success
            setNotification({ color: 'green', message: 'Worker created successfully.' });
            setTimeout(() => navigate('/admin/workers'), 1500); // Redirect after 1.5s
        } catch (err) {
            setNotification({ color: 'red', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: 500 }}>
            <Text size="xl" fw={700} mb="lg">Add New Worker</Text>
            
            {notification && (
                <Notification 
                    color={notification.color} 
                    icon={notification.color === 'green' ? <IconCheck size={18}/> : <IconX size={18}/>}
                    onClose={() => setNotification(null)}
                    mb="md"
                    title="Status"
                >
                    {notification.message}
                </Notification>
            )}

            <Paper withBorder p="xl" radius="md">
                <TextInput
                    label="Full Name"
                    placeholder="John Doe"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    mb="md"
                />
                
                <DatePickerInput
                    label="Pass Expiration Date"
                    placeholder="Pick date"
                    required
                    value={formData.expiration_date}
                    onChange={(date) => setFormData({...formData, expiration_date: date})}
                    mb="md"
                />

                <FileInput
                    label="Face Verification Photo"
                    placeholder="Upload .jpg/.png"
                    leftSection={<IconUpload size={14} />}
                    required
                    value={formData.file}
                    onChange={(file) => setFormData({...formData, file: file})}
                    mb="xl"
                />

                <Button fullWidth size="md" onClick={handleSubmit} loading={loading}>
                    Create Pass
                </Button>
            </Paper>
        </div>
    );
}