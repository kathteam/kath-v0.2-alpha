import { Breakpoint, useMediaQuery, useTheme } from '@mui/material';

/**
 * Custom hook for responsive design utilities.
 *
 * @description This hook provides utilities to check the current screen size
 * and determine which breakpoint the application is currently at. It uses
 * Material-UI's `useMediaQuery` and theme breakpoints for responsive behavior.
 *
 * @returns {object} An object containing responsive utility functions:
 * - `isMobile`: true if screen width is below 'sm' breakpoint (< 600px)
 * - `isTablet`: true if screen width is between 'sm' and 'md' (600px - 899px)
 * - `isDesktop`: true if screen width is 'md' or above (>= 900px)
 * - `isLargeDesktop`: true if screen width is 'lg' or above (>= 1200px)
 * - `up(breakpoint)`: returns true if screen width is at or above the specified breakpoint
 * - `down(breakpoint)`: returns true if screen width is below the specified breakpoint
 * - `between(start, end)`: returns true if screen width is between start and end breakpoints
 * - `only(breakpoint)`: returns true if screen width matches only the specified breakpoint
 *
 * @example
 * const { isMobile, isDesktop, up } = useResponsive();
 *
 * return (
 *   <Box sx={{ width: isMobile ? '100%' : '80%' }}>
 *     {isDesktop && <DesktopComponent />}
 *     {isMobile && <MobileComponent />}
 *   </Box>
 * );
 */
export const useResponsive = () => {
  const theme = useTheme();

  // Predefined breakpoint queries
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const isLargeDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  // Utility functions for custom breakpoint queries
  const up = (breakpoint: Breakpoint) => useMediaQuery(theme.breakpoints.up(breakpoint));
  const down = (breakpoint: Breakpoint) => useMediaQuery(theme.breakpoints.down(breakpoint));
  const between = (start: Breakpoint, end: Breakpoint) => useMediaQuery(theme.breakpoints.between(start, end));
  const only = (breakpoint: Breakpoint) => useMediaQuery(theme.breakpoints.only(breakpoint));

  return {
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    up,
    down,
    between,
    only,
  };
};
