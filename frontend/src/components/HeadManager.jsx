import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { renderToStaticMarkup } from 'react-dom/server';
import { IconShieldLock } from '@tabler/icons-react';

export default function HeadManager() {
  const location = useLocation();

  useEffect(() => {
    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.getElementsByTagName('head')[0].appendChild(link);
    }

    const isAdmin = location.pathname.startsWith('/admin');

    if (isAdmin) {
      document.title = 'QREC Admin Panel';
      
      const svgString = renderToStaticMarkup(<IconShieldLock color="#228be6" size={64} />);
      link.href = `data:image/svg+xml,${encodeURIComponent(svgString)}`;
      
    } else {
      document.title = 'QREC';
      link.href = '/red.svg'; 
    }

  }, [location]);

  return null; 
}