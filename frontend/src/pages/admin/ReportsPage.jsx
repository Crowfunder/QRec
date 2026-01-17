import React from 'react';
import { Center, Text, ThemeIcon } from '@mantine/core';
import { IconFileAnalytics } from '@tabler/icons-react';

export default function ReportsPage() {
  return (
    <Center h={400} style={{ flexDirection: 'column' }}>
      <ThemeIcon size={60} radius="xl" variant="light" mb="md">
        <IconFileAnalytics size={30} />
      </ThemeIcon>
      <Text size="xl" fw={700} c="dimmed">Reports Module</Text>
      <Text c="dimmed">Feature coming soon...</Text>
    </Center>
  );
}