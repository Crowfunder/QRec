import React from 'react';
import { AppShell, Text, Group, NavLink, Burger, useMantineTheme } from '@mantine/core';
import { IconUsers, IconUserPlus, IconFileAnalytics, IconShieldLock } from '@tabler/icons-react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useDisclosure } from '@mantine/hooks';

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useMantineTheme();
  const [opened, { toggle }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 260,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <IconShieldLock size={30} color={theme.colors.blue[6]} />
          <Text fw={700} size="lg">Admin Panel</Text>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Text size="xs" fw={500} c="dimmed" mb="sm">MODULES</Text>
        
        <NavLink 
            label="Worker List" 
            description="Edit & Invalidate"
            leftSection={<IconUsers size={20} />} 
            active={location.pathname === '/admin/workers'}
            onClick={() => { navigate('/admin/workers'); toggle(); }}
            color="blue"
            variant="filled"
        />

        <NavLink 
            label="Add Worker" 
            description="Create new pass"
            leftSection={<IconUserPlus size={20} />} 
            active={location.pathname === '/admin/add-worker'}
            onClick={() => { navigate('/admin/add-worker'); toggle(); }}
            color="green"
            variant="filled"
            mt="sm"
        />

        <NavLink 
            label="Reports" 
            leftSection={<IconFileAnalytics size={20} />} 
            active={location.pathname === '/admin/reports'}
            onClick={() => { navigate('/admin/reports'); toggle(); }}
            mt="sm"
        />
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}