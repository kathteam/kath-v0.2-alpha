# Responsive Design Testing Guide

A practical guide for testing the KATH application's responsive design across different devices and screen sizes.

---

## Quick Start

### Option 1: Browser DevTools (Recommended for Quick Testing)

**Chrome/Edge**:

1. Open <http://localhost:5173> (or production URL)
2. Press `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (Mac)
3. Click the device toolbar icon or press `Ctrl+Shift+M` / `Cmd+Shift+M`
4. Select a device preset or enter custom dimensions

**Firefox**:

1. Open <http://localhost:5173>
2. Press `F12` or `Ctrl+Shift+I` / `Cmd+Option+I`
3. Click the responsive design mode icon or press `Ctrl+Shift+M` / `Cmd+Shift+M`
4. Select dimensions or device

### Option 2: Real Devices (Recommended for Final Testing)

1. Ensure your dev server is running: `npm run dev`
2. Find your local IP address:
   - **Mac/Linux**: `ifconfig | grep "inet "` or `ip addr show`
   - **Windows**: `ipconfig`
3. On your mobile device, open browser to: `http://[YOUR_IP]:5173`
4. Example: `http://192.168.1.100:5173`

---

## Test Breakpoints

Test at these specific widths to verify behavior at breakpoint boundaries:

| Breakpoint | Width | Category | Expected Behavior |
|------------|-------|----------|-------------------|
| **xs** | 375px | Mobile Portrait | Drawer navigation, vertical stack, adjusted heights |
| **sm** | 600px | Mobile Landscape | Drawer navigation, optimized for landscape |
| **md** | 900px | Tablet | Desktop layout starts, inline sidebar |
| **lg** | 1200px | Desktop | Full desktop layout, optimal spacing |
| **xl** | 1536px | Large Desktop | Extended desktop layout |

### Critical Test Points

- **599px** - Just below tablet breakpoint (should show drawer)
- **600px** - At tablet breakpoint (should show drawer)
- **899px** - Just below desktop breakpoint (should show drawer)
- **900px** - At desktop breakpoint (should show inline sidebar)

---

## Detailed Test Checklist

### Mobile Portrait (375px - iPhone SE)

**Layout**:

- [ ] Menu button visible in top-left corner
- [ ] Menu button is exactly 44x44px (WCAG compliant)
- [ ] No sidebar visible by default
- [ ] Content uses full width
- [ ] Components stacked vertically
- [ ] No border radius on screen edges

**Navigation**:

- [ ] Tap menu button  drawer slides in from left
- [ ] Drawer covers ~80% of screen width
- [ ] File tree visible and functional in drawer
- [ ] Close button (X) visible in drawer (44x44px)
- [ ] Tap close button  drawer closes
- [ ] Tap backdrop (dark area)  drawer closes
- [ ] Smooth slide animation (no jank)

**Component Heights** (approximate):

- [ ] Toolbar: ~15% of screen height
- [ ] Editor: ~55% of screen height
- [ ] Filebar: ~2% of screen height
- [ ] Console: ~28% of screen height

**Interactions**:

- [ ] All buttons are at least 44x44px
- [ ] Icon buttons are at least 44x44px
- [ ] Comfortable tap targets with spacing
- [ ] No accidental double-taps needed
- [ ] Text is readable without zooming
- [ ] Form inputs are easily tappable

**Scrolling**:

- [ ] Data grid scrolls horizontally if needed
- [ ] File tabs scroll horizontally if many files open
- [ ] Toolbar scrolls vertically if content overflows
- [ ] Console scrolls vertically for long output
- [ ] No unexpected horizontal scrolling on main container

**Visual**:

- [ ] No layout shifts when drawer opens/closes
- [ ] No content cut off or overlapping
- [ ] Colors and contrast are good
- [ ] Icons are clear and recognizable

### Mobile Landscape (640x360 - iPhone SE rotated)

**Layout**:

- [ ] Menu button still visible
- [ ] Drawer opens to ~300px width (not 80%)
- [ ] More horizontal space for content
- [ ] Vertical space is limited but usable

**Usability**:

- [ ] Toolbar doesn't take up too much vertical space
- [ ] Editor area is still functional
- [ ] Console is not too compressed

### Tablet Portrait (768px - iPad Mini)

**Layout**:

- [ ] Menu button visible in top-left
- [ ] Menu button is 44x44px
- [ ] Content uses full width
- [ ] Drawer opens to 300px width (not 80%)

**Navigation**:

- [ ] Drawer opens/closes smoothly
- [ ] File tree is comfortable to navigate
- [ ] Touch targets are properly sized
- [ ] No accidental taps

**Component Sizing**:

- [ ] Toolbar has more breathing room
- [ ] Editor grid shows more columns
- [ ] Console has comfortable height
- [ ] All components scale nicely

### Tablet Landscape (1024px - iPad)

**Layout**:

- [ ] Desktop layout should appear at 900px+
- [ ] Inline sidebar visible (no menu button)
- [ ] Side-by-side layout (20% sidebar, 80% content)
- [ ] Rounded corners on components

**Transition**:

- [ ] Test at 899px (drawer)  900px (inline sidebar)
- [ ] Layout shifts smoothly without breaking
- [ ] No flashing or jarring transitions

### Desktop (1440px - Standard Laptop)

**Layout**:

- [ ] Inline sidebar on left (20% width)
- [ ] File tree always visible
- [ ] Main content area (80% width)
- [ ] Rounded corners on all components
- [ ] No menu button anywhere

**Component Heights** (desktop):

- [ ] Toolbar: ~25% of screen height
- [ ] Editor: ~50% of screen height
- [ ] Filebar: ~3% of screen height
- [ ] Console: ~22% of screen height

**Spacing**:

- [ ] Comfortable margins around components
- [ ] Adequate padding inside components
- [ ] Visual hierarchy is clear
- [ ] No wasted space

**Hover Effects**:

- [ ] Buttons show hover state
- [ ] File tree items highlight on hover
- [ ] Data grid rows highlight on hover
- [ ] Cursor changes appropriately (pointer, default)

### Large Desktop (1920px - Full HD)

**Layout**:

- [ ] Layout scales proportionally
- [ ] No excessive white space
- [ ] Components don't look stretched
- [ ] Sidebar remains ~20% (not too wide)
- [ ] Content area uses available space well

**Readability**:

- [ ] Text is not too small
- [ ] Buttons are not tiny
- [ ] Comfortable viewing distance

---

## Browser Compatibility Testing

Test in these browsers (minimum versions):

### Desktop Browsers

- [ ] Chrome 90+ (Windows/Mac/Linux)
- [ ] Edge 90+ (Windows/Mac)
- [ ] Firefox 88+ (Windows/Mac/Linux)
- [ ] Safari 14+ (Mac)

### Mobile Browsers

- [ ] Safari Mobile (iOS 14+) - iPhone
- [ ] Safari Mobile (iOS 14+) - iPad
- [ ] Chrome Mobile (Android 10+)
- [ ] Samsung Internet (latest)

### Key Tests Per Browser

- [ ] Layout renders correctly
- [ ] Drawer opens/closes smoothly
- [ ] Touch interactions work
- [ ] No console errors
- [ ] Transitions are smooth

---

## Accessibility Testing

### Keyboard Navigation

- [ ] Press `Tab`  focus moves to menu button (if visible)
- [ ] Press `Enter` or `Space`  drawer opens
- [ ] Press `Tab`  focus moves through drawer elements
- [ ] Press `Escape`  drawer closes
- [ ] Focus returns to menu button after drawer closes
- [ ] All interactive elements are reachable via keyboard
- [ ] Focus indicators are visible
- [ ] Tab order is logical

### Screen Reader Testing (Optional)

- [ ] Menu button announced as "Open file navigation"
- [ ] Close button announced as "Close file navigation"
- [ ] Drawer state changes are announced
- [ ] File tree items are properly labeled
- [ ] All buttons have descriptive labels

### Touch Target Size (WCAG 2.1 Level AAA)

- [ ] All buttons are minimum 44x44px
- [ ] Icon buttons are minimum 44x44px
- [ ] Adequate spacing between tap targets (at least 8px)
- [ ] No accidental activations

### Color Contrast

- [ ] Text is readable on all backgrounds
- [ ] Icons are clearly visible
- [ ] Focus indicators are visible
- [ ] Dark mode (if applicable) has good contrast

---

## Performance Testing

### Smooth Animations

- [ ] Drawer slides smoothly (no stuttering)
- [ ] Layout transitions are smooth at breakpoints
- [ ] No visual glitches or flashing
- [ ] Frame rate stays above 30fps (ideally 60fps)

### Touch Response

- [ ] Taps register immediately (< 300ms)
- [ ] No lag when opening drawer
- [ ] Scrolling is smooth (not janky)
- [ ] No delayed button responses

### Load Time

- [ ] Initial page load < 3s on 3G
- [ ] Responsive layout applies immediately
- [ ] No layout shifts after load (CLS)

---

## Common Issues & Troubleshooting

### Issue: Menu button doesn't appear on mobile

**Check**:

- Screen width is < 900px
- DevTools device mode is enabled
- Browser zoom is at 100%
- useResponsive hook is imported correctly

**Fix**: Refresh page, check console for errors

### Issue: Drawer doesn't open when menu button is clicked

**Check**:

- Console for JavaScript errors
- Event listeners are attached
- State is updating correctly

**Fix**: Check browser console, verify MobileDrawer component is rendering

### Issue: Layout looks broken at specific width

**Check**:

- Test at exact breakpoint values (600px, 900px)
- Check if you're between breakpoints
- Verify CSS is loaded correctly

**Fix**: Test at breakpoint boundaries, check for CSS conflicts

### Issue: Buttons too small on mobile

**Check**:

- Theme overrides are applied (MuiButton, MuiIconButton)
- Browser DevTools computed styles show min-width/height: 44px
- No conflicting CSS

**Fix**: Verify theme configuration, clear cache and reload

### Issue: Content overflows or is cut off

**Check**:

- Parent containers have proper overflow settings
- Heights sum to 100% or less
- No absolute positioning conflicts

**Fix**: Add overflow: auto to containers, check height calculations

### Issue: Drawer animation is choppy

**Check**:

- GPU acceleration is enabled
- No heavy operations during animation
- Frame rate in DevTools Performance tab

**Fix**: Simplify component tree, reduce re-renders, use CSS transforms

---

## Test Report Template

Use this template to document your testing:

```markdown
# Responsive Design Test Report

**Date**: [Date]
**Tester**: [Name]
**Browser**: [Chrome 120, Safari 17, etc.]
**Device**: [Physical device or DevTools]

## Mobile Portrait (375px)
- [ ] Layout: PASS/FAIL
- [ ] Navigation: PASS/FAIL
- [ ] Interactions: PASS/FAIL
- **Issues**: [List any issues]

## Mobile Landscape (640px)
- [ ] Layout: PASS/FAIL
- [ ] Usability: PASS/FAIL
- **Issues**: [List any issues]

## Tablet Portrait (768px)
- [ ] Layout: PASS/FAIL
- [ ] Navigation: PASS/FAIL
- **Issues**: [List any issues]

## Tablet Landscape (1024px)
- [ ] Layout: PASS/FAIL
- [ ] Transition: PASS/FAIL
- **Issues**: [List any issues]

## Desktop (1440px)
- [ ] Layout: PASS/FAIL
- [ ] Spacing: PASS/FAIL
- [ ] Hover Effects: PASS/FAIL
- **Issues**: [List any issues]

## Accessibility
- [ ] Keyboard Navigation: PASS/FAIL
- [ ] Touch Targets: PASS/FAIL
- **Issues**: [List any issues]

## Overall Rating: [PASS/FAIL]
**Critical Issues**: [Count]
**Minor Issues**: [Count]
**Notes**: [Additional observations]
```

---

## Automated Testing (Future)

For Phase 2+, consider adding automated responsive tests:

### Playwright Example

```typescript
test('mobile navigation drawer works', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:5173');

  // Menu button should be visible
  await expect(page.locator('[aria-label="Open file navigation"]')).toBeVisible();

  // Click menu button
  await page.click('[aria-label="Open file navigation"]');

  // Drawer should open
  await expect(page.locator('.MuiDrawer-root')).toBeVisible();

  // File tree should be visible in drawer
  await expect(page.locator('text=Import file')).toBeVisible();

  // Close drawer
  await page.click('[aria-label="Close file navigation"]');
  await expect(page.locator('.MuiDrawer-root')).not.toBeVisible();
});

test('desktop shows inline sidebar', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173');

  // Menu button should NOT be visible
  await expect(page.locator('[aria-label="Open file navigation"]')).not.toBeVisible();

  // File tree should be visible inline
  await expect(page.locator('text=Import file')).toBeVisible();
});
```

---

## Resources

- [KATH Responsive Design Documentation](./RESPONSIVE_DESIGN.md)
- [Material-UI Breakpoints](https://mui.com/material-ui/customization/breakpoints/)
- [WCAG Touch Target Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)
- [Chrome DevTools Device Mode](https://developer.chrome.com/docs/devtools/device-mode/)
- [Firefox Responsive Design Mode](https://firefox-source-docs.mozilla.org/devtools-user/responsive_design_mode/)

---

## Questions or Issues?

If you encounter issues during testing:

1. Check the browser console for errors
2. Verify your viewport size in DevTools
3. Clear browser cache and reload
4. Review the [Responsive Design Documentation](./RESPONSIVE_DESIGN.md)
5. Create an issue in the project repository with screenshots

Happy testing! 
