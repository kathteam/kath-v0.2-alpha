# Responsive Design Implementation

This document describes the responsive design implementation for the KATH frontend application.

## Overview

The KATH application now features a fully responsive design that adapts to different screen sizes:
- **Desktop (900px)**: Full side-by-side layout with fixed sidebar
- **Tablet (600-899px)**: Collapsible drawer for file tree, optimized content layout
- **Mobile (<600px)**: Drawer navigation, vertically stacked components, touch-friendly interactions

## Breakpoints

The application uses Material-UI's standard breakpoints:

```typescript
xs: 0      // Mobile portrait (< 600px)
sm: 600    // Mobile landscape / small tablets (600-899px)
md: 900    // Tablets (900-1199px)
lg: 1200   // Desktop (1200-1535px)
xl: 1536   // Large desktop ( 1536px)
```

Configured in: `src/stores/themeContextProvider.tsx`

## Key Features

### 1. Responsive Hook

**Location**: `src/hooks/useResponsive.ts`

A custom hook that provides responsive utilities:

```typescript
import { useResponsive } from '@/hooks';

const { isMobile, isTablet, isDesktop, up, down, between, only } = useResponsive();

// Usage examples
if (isMobile) {
  // Mobile-specific behavior
}

if (up('md')) {
  // Desktop and above
}

if (between('sm', 'md')) {
  // Tablet only
}
```

**Available utilities**:
- `isMobile`: boolean - true for screens < 600px
- `isTablet`: boolean - true for screens 600-899px
- `isDesktop`: boolean - true for screens  900px
- `isLargeDesktop`: boolean - true for screens  1200px
- `up(breakpoint)`: function - check if screen is at or above breakpoint
- `down(breakpoint)`: function - check if screen is below breakpoint
- `between(start, end)`: function - check if screen is between two breakpoints
- `only(breakpoint)`: function - check if screen matches specific breakpoint

### 2. Mobile Navigation Drawer

**Location**: `src/features/editor/components/MobileDrawer.tsx`

A responsive wrapper that provides:
- **Desktop (900px)**: Inline file tree sidebar (20% width)
- **Mobile/Tablet (<900px)**: Collapsible drawer navigation

**Features**:
- Touch-friendly menu button (44x44px minimum)
- Close button inside drawer
- Backdrop click to close
- Smooth transitions
- Accessible ARIA labels

**Usage**:
```typescript
import { MobileDrawer } from '@/features/editor/components';

<MobileDrawer>
  <YourMainContent />
</MobileDrawer>
```

### 3. Responsive Editor Layout

**Location**: `src/features/editor/index.tsx`

The main editor layout adapts responsively:

**Desktop (900px)**:
- Side-by-side layout (20% sidebar, 80% content)
- Fixed sidebar with file tree
- Standard component heights

**Tablet (600-899px)**:
- Drawer navigation for file tree
- Full-width content area
- Optimized heights for touch interaction

**Mobile (<600px)**:
- Drawer navigation
- Full-width components
- Vertically stacked layout
- Adjusted height ratios:
  - Toolbar: 15% (vs 25% desktop)
  - Editor: 55% (vs 50% desktop)
  - Filebar: 2% (vs 3% desktop)
  - Console: 28% (vs 22% desktop)
- No border radius on edges
- Horizontal scrolling enabled for data grid and file tabs
- Vertical scrolling enabled for toolbar and console

### 4. Touch-Friendly Interactions

**Location**: `src/stores/themeContextProvider.tsx`

All interactive elements meet WCAG touch target size guidelines (minimum 44x44px):

**Buttons**:
```typescript
MuiButton: {
  styleOverrides: {
    root: {
      minHeight: '44px',
      minWidth: '44px',
      padding: '10px 16px',
    },
  },
}
```

**Icon Buttons**:
```typescript
MuiIconButton: {
  styleOverrides: {
    root: {
      minWidth: '44px',
      minHeight: '44px',
      padding: '10px',
    },
  },
}
```

## Implementation Guidelines

### Using the Responsive Hook

1. **Import the hook**:
```typescript
import { useResponsive } from '@/hooks';
```

2. **Use in your component**:
```typescript
const MyComponent = () => {
  const { isMobile, isDesktop } = useResponsive();

  return (
    <Box sx={{
      width: isMobile ? '100%' : '80%',
      padding: isMobile ? '0.5rem' : '1rem'
    }}>
      {isMobile ? <MobileView /> : <DesktopView />}
    </Box>
  );
};
```

3. **Use with MUI sx prop**:
```typescript
<Box sx={{
  display: { xs: 'block', md: 'flex' },
  flexDirection: { xs: 'column', md: 'row' },
  gap: { xs: 1, sm: 2, md: 3 }
}}>
  {/* Content */}
</Box>
```

### Adding Responsive Styles

**Method 1: Responsive Hook**
```typescript
const { isMobile } = useResponsive();

<Component style={{
  fontSize: isMobile ? '14px' : '16px'
}} />
```

**Method 2: MUI Breakpoint Syntax** (recommended for styling)
```typescript
<Box sx={{
  fontSize: { xs: '14px', md: '16px' },
  padding: { xs: 1, sm: 2, md: 3 },
  display: { xs: 'none', md: 'block' }
}} />
```

**Method 3: Theme Breakpoints**
```typescript
const theme = useTheme();

<Box sx={{
  [theme.breakpoints.down('sm')]: {
    display: 'none',
  },
  [theme.breakpoints.up('md')]: {
    display: 'block',
  }
}} />
```

## Testing Responsive Design

### Browser Developer Tools

1. **Chrome/Edge DevTools**:
   - Press `F12` or `Ctrl+Shift+I`
   - Click the device toolbar icon (or `Ctrl+Shift+M`)
   - Select device presets or set custom dimensions

2. **Firefox DevTools**:
   - Press `F12` or `Ctrl+Shift+I`
   - Click the responsive design mode icon (or `Ctrl+Shift+M`)
   - Select device presets or custom dimensions

### Test Breakpoints

Test at these key widths:
- **375px**: iPhone SE (mobile portrait)
- **768px**: iPad portrait (tablet)
- **1024px**: iPad landscape (tablet/small desktop)
- **1440px**: Standard desktop
- **1920px**: Full HD desktop

### Checklist

- [ ] Menu button appears on mobile/tablet (<900px)
- [ ] Drawer opens and closes smoothly
- [ ] File tree is accessible in drawer
- [ ] All buttons are at least 44x44px
- [ ] Text is readable at all sizes
- [ ] No horizontal scrolling on mobile (except for data grid/tabs)
- [ ] Content doesn't overflow containers
- [ ] Touch interactions work smoothly
- [ ] Transitions are smooth
- [ ] Layout doesn't break at breakpoints

## Performance Considerations

1. **useMediaQuery hooks are efficient**: They use CSS media queries internally and only re-render when breakpoint changes

2. **Minimize layout shifts**: Pre-define heights and widths to avoid content jumping during responsive changes

3. **Lazy load heavy components**: Use React.lazy() for components not immediately visible on mobile

4. **Optimize images**: Use responsive images with `srcset` for different screen sizes

## Accessibility

The responsive design maintains accessibility:

- **Touch targets**: All interactive elements are minimum 44x44px (WCAG 2.1 Level AAA)
- **ARIA labels**: Menu and close buttons have descriptive labels
- **Keyboard navigation**: Drawer can be closed with Escape key
- **Focus management**: Focus is trapped in drawer when open
- **Screen readers**: All interactive elements are properly labeled

## Browser Support

Tested and supported on:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Safari (iOS 14+)
- Chrome Mobile (Android 10+)

## Future Enhancements

Planned improvements for Phase 2:
- Landscape mode optimizations for tablets
- Split-screen mode for large desktops
- Custom breakpoints for ultra-wide displays
- Touch gestures (swipe, pinch-to-zoom)
- Responsive data grid column sizing
- Adaptive component density based on screen size

## Troubleshooting

### Issue: Drawer doesn't open on mobile

**Solution**: Check that `useResponsive` hook is properly imported and `isMobile` or `isTablet` is true.

### Issue: Layout breaks at specific width

**Solution**: Test at the breakpoint boundaries (600px, 900px, 1200px) and adjust conditional logic or sx props.

### Issue: Buttons too small on touch devices

**Solution**: Verify theme overrides are applied. Check browser developer tools computed styles.

### Issue: Content overflows on mobile

**Solution**: Add `overflowX: 'auto'` or `overflowY: 'auto'` to container Box components.

## Resources

- [Material-UI Breakpoints](https://mui.com/material-ui/customization/breakpoints/)
- [Material-UI useMediaQuery](https://mui.com/material-ui/react-use-media-query/)
- [WCAG Touch Target Size](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)
- [Responsive Design Best Practices](https://web.dev/responsive-web-design-basics/)

## Files Changed/Created

### Created
- `src/hooks/useResponsive.ts` - Custom responsive hook
- `src/features/editor/components/MobileDrawer.tsx` - Responsive navigation drawer
- `RESPONSIVE_DESIGN.md` - This documentation

### Modified
- `src/stores/themeContextProvider.tsx` - Added breakpoints and touch-friendly button sizes
- `src/features/editor/index.tsx` - Made editor layout responsive
- `src/hooks/index.ts` - Export useResponsive hook
- `src/features/editor/components/index.ts` - Export MobileDrawer component

## Contact

For questions or issues related to responsive design, please refer to the KATH project documentation or create an issue in the project repository.
