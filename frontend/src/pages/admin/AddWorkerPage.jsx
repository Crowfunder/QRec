import React, { useState } from 'react';
import { TextInput, FileInput, Button, Paper, Text, Notification, Group, Modal, Image, Center } from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconUpload, IconCheck, IconX, IconPrinter, IconDownload } from '@tabler/icons-react';
import { workerApi } from '../../services/workerApi';
import { useNavigate } from 'react-router-dom';
import printJS from 'print-js';

export default function AddWorkerPage() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
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
            setNotification({ color: 'red', message: 'Fill in the name and photo!' });
            return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0); 
        const selectedDate = new Date(formData.expiration_date);
        selectedDate.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            setNotification({ color: 'red', message: 'Expiration date cannot be in the past!' });
            return;
        }

        setLoading(true);
        try {
            const newWorker = await workerApi.create(formData.name, formData.expiration_date, formData.file);
            
            setNotification({ color: 'green', message: 'Employee added. Generating pass...' });

            const imageBlob = await workerApi.getEntryPass(newWorker.id);
            const imageUrl = URL.createObjectURL(imageBlob);
            
            setPassImage(imageUrl);
            setPassModalOpen(true);

        } catch (err) {
            setNotification({ color: 'red', message: err.message });
        } finally {
            setLoading(false);
        }
    };

    const handleCloseModal = () => {
        setPassModalOpen(false);
        navigate('/admin/workers');
    };

    const handlePrint = () => {
        if (!passImage) return;

        printJS({
            printable: passImage,
            type: 'image', 
            header: `QR Code for worker\n${formData.name}`,
            imageStyle: 'width:100%; margin-bottom:20px;'
        });
    };

    const handleDownload = () => {
        if (!passImage) return;

        const link = document.createElement('a');
        link.href = passImage;
        const safeName = formData.name.replace(/\s+/g, '_'); 
        link.download = `Pass_${safeName}.png`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div style={{ maxWidth: 500 }}>
            <Text size="xl" fw={700} mb="lg">Add New Employee</Text>
            
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
                    label="First and Last Name"
                    placeholder="John Doe"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    mb="md"
                />
                
                <DatePickerInput
                    label="Pass Expiration Date"
                    placeholder="Select date"
                    required
                    value={formData.expiration_date}
                    onChange={(date) => setFormData({...formData, expiration_date: date})}
                    mb="md"
                />

                <FileInput
                    label="Face Photo (Verification)"
                    placeholder="Select .jpg/.png file"
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
                title="Generated Pass"
                size="lg"
                centered
            >
                <Center>
                    {passImage && <Image src={passImage} alt="Entry Pass" radius="md" style={{ maxHeight: '60vh' }} />}
                </Center>
                
                <Group justify="center" mt="xl">
                    <Button 
                        leftSection={<IconPrinter size={20}/>} 
                        onClick={handlePrint} 
                        variant="default"
                    >
                        Print
                    </Button>

                    <Button 
                        leftSection={<IconDownload size={20}/>} 
                        onClick={handleDownload}
                        color="blue"
                    >
                        Download QR Code
                    </Button>

                    <Button variant="subtle" onClick={handleCloseModal}>
                        Close
                    </Button>
                </Group>
            </Modal>
        </div>
    );
}