import { ConsoleView, EditorView, FilebarView, ToolbarView } from '@/features/editor/components';
import { MobileDrawer } from '@/features/editor/components/MobileDrawer';
import { WorkspaceContextProvider } from '@/features/editor/stores';
import { useResponsive } from '@/hooks/useResponsive';
import { Box, useTheme } from '@mui/material';

/**
 * `Editor` component sets up the main layout for the editor application, integrating various UI components within a responsive
 * flexbox layout.
 *
 * @description This component uses Material-UI's `Box` component to create a flexible layout for the editor interface. It
 * integrates multiple sub-components, including `FileTreeView`, `Toolbar`, `EditorView`, `FilebarView`, and `Console`, each
 * occupying a specific region of the layout. The component also provides a context for workspace management using
 * `WorkspaceContextProvider`.
 *
 * The layout is structured as follows:
 * - A sidebar on the left (`20%` width on desktop, drawer on mobile) containing the `FileTreeView` component.
 * - A main content area that includes:
 *   - A `ToolbarView` at the top.
 *   - An `EditorView` in the middle.
 *   - A `FilebarView` above the console.
 *   - A `ConsoleView` component at the bottom with rounded corners.
 *
 * The layout adapts responsively:
 * - **Desktop (900px)**: Side-by-side layout with fixed sidebar (20%) and main content (80%)
 * - **Tablet (600-899px)**: Collapsible drawer for file tree, stacked main content
 * - **Mobile (<600px)**: Drawer for file tree, vertically stacked components, adjusted heights
 *
 * The layout is styled using the current theme's colors and responsive design principles. The theme controls the background
 * colors, border-radius, and other styling aspects, making the layout adapt to light and dark modes seamlessly.
 *
 * @component
 *
 * @example
 * // Example usage of the Editor component
 * return (
 *   <Editor />
 * );
 *
 * @returns {JSX.Element} The rendered editor layout with integrated components and workspace context.
 */
export const Editor = () => {
  const theme = useTheme();
  const { isMobile, isTablet } = useResponsive();

  // Adjust heights based on screen size
  const toolbarHeight = isMobile ? '15%' : '25%';
  const editorHeight = isMobile ? '55%' : '50%';
  const filebarHeight = isMobile ? '2%' : '3%';
  const consoleHeight = isMobile ? '28%' : '22%';

  return (
    <WorkspaceContextProvider>
      <MobileDrawer>
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            ...(isMobile || isTablet
              ? {
                  margin: 0,
                }
              : {
                  width: '75vw',
                }),
          }}
        >
          <Box
            sx={{
              width: '100%',
              height: toolbarHeight,
              display: 'flex',
              flexDirection: 'column',
              bgcolor: theme.palette.action.selected,
              borderRadius: isMobile ? 0 : '0 0.625rem 0 0',
              overflowY: 'auto', // Allow scrolling on mobile if content overflows
            }}
          >
            <ToolbarView />
          </Box>
          <Box
            sx={{
              width: '100%',
              height: editorHeight,
              display: 'flex',
              flexDirection: 'column',
              bgcolor: theme.palette.background.default,
              overflowX: 'auto', // Allow horizontal scrolling for data grid on mobile
            }}
          >
            <EditorView />
          </Box>
          <Box
            sx={{
              width: '100%',
              height: filebarHeight,
              display: 'flex',
              flexDirection: 'row',
              bgcolor: theme.palette.action.selected,
              overflowX: 'auto', // Allow horizontal scrolling for file tabs on mobile
            }}
          >
            <FilebarView />
          </Box>
          <Box
            sx={{
              width: '100%',
              height: consoleHeight,
              display: 'flex',
              flexDirection: 'column',
              bgcolor: theme.palette.background.paper,
              borderRadius: isMobile ? 0 : '0 0 0.625rem 0',
              overflowY: 'auto', // Allow scrolling for console output
            }}
          >
            <ConsoleView />
          </Box>
        </Box>
      </MobileDrawer>
    </WorkspaceContextProvider>
  );
};
