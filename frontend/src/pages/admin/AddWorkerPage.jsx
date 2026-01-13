import React, { useState } from 'react';
import { TextInput, FileInput, Button, Paper, Text, Notification, Group, Modal, Image, Center } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconUpload, IconCheck, IconX, IconPrinter } from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';
import { useNavigate } from 'react-router-dom';

export default function AddWorkerPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    
    // Form State
    const [formData, setFormData] = useState({
        name: '',
        expiration_date: new Date(),
        file: null
    });
    const [notification, setNotification] = useState(null);
    const [passImage, setPassImage] = useState(null);
    const [passModalOpen, setPassModalOpen] = useState(false);

    const handleSubmit = async () => {
        if (!formData.name || !formData.file) {
            setNotification({ color: 'red', message: 'Name and Photo are required!' });
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0); // Reset time to start of day for fair comparison
        const selectedDate = new Date(formData.expiration_date);
        selectedDate.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            setNotification({ color: 'red', message: 'Expiration date cannot be in the past!' });
            return;
        }

        setLoading(true);
        try {
            // 1. Create the Worker
            const newWorker = await workerApi.create(formData.name, formData.expiration_date, formData.file);
            
            setNotification({ color: 'green', message: 'Worker created successfully. Generating Pass...' });

            // 2. Fetch the Entry Pass Image
            const imageBlob = await workerApi.getEntryPass(newWorker.id);
            
            // 3. Convert Blob to URL for display
            const imageUrl = URL.createObjectURL(imageBlob);
            setPassImage(imageUrl);
            setPassModalOpen(true); 

        } catch (err) {
            setNotification({ color: 'red', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    // Clean up when closing modal
    const handleCloseModal = () => {
        setPassModalOpen(false);
        navigate('/admin/workers');
    };

    // Print helper
    const handlePrint = () => {
        const printWindow = window.open(passImage);
        printWindow.print();
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

            <Modal 
                opened={passModalOpen} 
                onClose={handleCloseModal} 
                title="Entry Pass Generated"
                size="lg"
            >
                <Center>
                    {passImage && <Image src={passImage} alt="Entry Pass" radius="md" />}
                </Center>
                <Group justify="center" mt="md">
                    <Button leftSection={<IconPrinter size={16}/>} onClick={handlePrint}>
                        Print Pass
                    </Button>
                    <Button variant="default" onClick={handleCloseModal}>
                        Done
                    </Button>
                </Group>
            </Modal>
        </div>
    );
}