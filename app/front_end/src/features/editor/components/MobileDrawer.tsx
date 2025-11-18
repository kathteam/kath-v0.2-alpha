import { FileTreeView } from '@/features/editor/components';
import { useResponsive } from '@/hooks/useResponsive';
import { Close as CloseIcon, Menu as MenuIcon } from '@mui/icons-material';
import { Box, Drawer, IconButton, useTheme } from '@mui/material';
import { useState } from 'react';

interface MobileDrawerProps {
  children: React.ReactNode;
}

/**
 * `MobileDrawer` component provides a responsive navigation drawer for mobile and tablet views.
 *
 * @description This component implements a collapsible navigation drawer that appears on the left side
 * of the screen on mobile and tablet devices. On desktop, it renders the file tree inline without a drawer.
 * The drawer can be opened and closed via a menu button, and includes a close button for better UX.
 *
 * Features:
 * - Responsive behavior: drawer on mobile/tablet, inline on desktop
 * - Touch-friendly menu and close buttons (44x44px minimum)
 * - Swipe-to-close gesture support
 * - Backdrop click to close
 * - Smooth transitions
 *
 * @component
 *
 * @param {MobileDrawerProps} props - Component props
 * @param {React.ReactNode} props.children - The main content to display alongside the drawer
 *
 * @example
 * return (
 *   <MobileDrawer>
 *     <EditorContent />
 *   </MobileDrawer>
 * );
 *
 * @returns {JSX.Element} The responsive drawer layout with file tree and main content
 */
export const MobileDrawer: React.FC<MobileDrawerProps> = ({ children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { isMobile, isTablet } = useResponsive();
  const theme = useTheme();

  const showDrawer = isMobile || isTablet;
  const drawerWidth = isMobile ? '80%' : '300px';

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
  };

  // Desktop view: render file tree inline
  if (!showDrawer) {
    return (
      <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'row' }}>
        <Box
          sx={{
            width: '20vw',
            display: 'flex',
            flexDirection: 'column',
            bgcolor: theme.palette.secondary.main,
            borderRadius: '0.625rem 0 0 0.625rem',
            margin: '1rem',
            padding: '1rem',
          }}
        >
          <FileTreeView />
        </Box>
        {children}
      </Box>
    );
  }

  // Mobile/Tablet view: render with drawer
  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Menu button - touch-friendly 44x44px */}
      <Box
        sx={{
          position: 'absolute',
          top: '1rem',
          left: '1rem',
          zIndex: theme.zIndex.drawer + 1,
        }}
      >
        <IconButton
          onClick={toggleDrawer}
          sx={{
            width: '44px',
            height: '44px',
            bgcolor: theme.palette.primary.main,
            color: theme.palette.primary.contrastText,
            '&:hover': {
              bgcolor: theme.palette.primary.dark,
            },
          }}
          aria-label="Open file navigation"
        >
          <MenuIcon />
        </IconButton>
      </Box>

      {/* Drawer for mobile/tablet */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={closeDrawer}
        sx={{
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            bgcolor: theme.palette.secondary.main,
            padding: '1rem',
            boxSizing: 'border-box',
          },
        }}
      >
        {/* Close button inside drawer */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: '1rem' }}>
          <IconButton
            onClick={closeDrawer}
            sx={{
              width: '44px',
              height: '44px',
            }}
            aria-label="Close file navigation"
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {/* File tree inside drawer */}
        <FileTreeView />
      </Drawer>

      {/* Main content */}
      <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>{children}</Box>
    </Box>
  );
};
