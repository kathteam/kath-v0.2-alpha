/**
 * VariantPagination Component
 *
 * Provides pagination controls and statistics for variant data display.
 * Supports:
 * - Navigation (previous, next, go-to-page)
 * - Page size selector (10, 25, 50, 100 entries per page)
 * - Real-time statistics display
 * - Responsive design
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Select,
  MenuItem,
  TextField,
  Typography,
  Stack,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Pagination,
  Card,
  CardContent,
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
} from '@mui/icons-material';

interface PaginationMetadata {
  current_page: number;
  page_size: number;
  total_entries: number;
  total_pages: number;
  has_previous: boolean;
  has_next: boolean;
  showing_from: number;
  showing_to: number;
}

interface VariantPaginationProps {
  pagination: PaginationMetadata;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  loading?: boolean;
  variant?: 'dense' | 'default';
}

/**
 * VariantPagination Component
 *
 * Displays pagination controls and statistics for variant data.
 *
 * @param pagination - Current pagination metadata
 * @param onPageChange - Callback when page changes
 * @param onPageSizeChange - Callback when page size changes
 * @param loading - Loading state
 * @param variant - Display variant (dense or default)
 */
const VariantPagination: React.FC<VariantPaginationProps> = ({
  pagination,
  onPageChange,
  onPageSizeChange,
  loading = false,
  variant = 'default',
}) => {
  const [goToPageInput, setGoToPageInput] = useState<string>('');

  // Reset go-to-page input when page changes
  useEffect(() => {
    setGoToPageInput('');
  }, [pagination.current_page]);

  const handleGoToPage = () => {
    const pageNum = parseInt(goToPageInput, 10);
    if (
      !isNaN(pageNum) &&
      pageNum >= 1 &&
      pageNum <= pagination.total_pages
    ) {
      onPageChange(pageNum - 1); // Convert to 0-indexed
      setGoToPageInput('');
    }
  };

  const handlePageSizeChange = (
    event: React.ChangeEvent<{ name?: string; value: unknown }>
  ) => {
    const newPageSize = event.target.value as number;
    onPageSizeChange(newPageSize);
  };

  const isDense = variant === 'dense';
  const spacing = isDense ? 1 : 2;
  const typographyVariant = isDense ? 'body2' : 'body1';

  return (
    <Paper
      elevation={isDense ? 0 : 1}
      sx={{
        p: spacing,
        mt: spacing,
        backgroundColor: isDense ? 'transparent' : '#f9f9f9',
        border: isDense ? '1px solid #e0e0e0' : 'none',
      }}
    >
      <Stack spacing={spacing}>
        {/* Statistics Row */}
        <Grid container spacing={spacing} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Typography variant={typographyVariant} sx={{ fontWeight: 500 }}>
              {pagination.total_entries > 0
                ? `Showing ${pagination.showing_from}–${pagination.showing_to} of ${pagination.total_entries.toLocaleString()} entries`
                : 'No entries'}
            </Typography>
          </Grid>

          {/* Page Size Selector */}
          <Grid item xs={12} sm={6} sx={{ display: 'flex', justifyContent: { xs: 'flex-start', sm: 'flex-end' } }}>
            <FormControl size={isDense ? 'small' : 'medium'} sx={{ minWidth: 150 }}>
              <InputLabel>Entries per page</InputLabel>
              <Select
                value={pagination.page_size}
                onChange={handlePageSizeChange}
                disabled={loading || pagination.total_entries === 0}
                label="Entries per page"
              >
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={25}>25</MenuItem>
                <MenuItem value={50}>50</MenuItem>
                <MenuItem value={100}>100</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Navigation Row */}
        {pagination.total_pages > 1 && (
          <Grid container spacing={spacing} alignItems="center">
            {/* Previous/Next Buttons */}
            <Grid item xs={12} sm="auto">
              <Stack direction="row" spacing={0.5}>
                <Button
                  size={isDense ? 'small' : 'medium'}
                  variant="outlined"
                  startIcon={<FirstPageIcon />}
                  onClick={() => onPageChange(0)}
                  disabled={!pagination.has_previous || loading}
                  sx={{ minWidth: isDense ? 'auto' : '100px' }}
                >
                  {!isDense && 'First'}
                </Button>

                <Button
                  size={isDense ? 'small' : 'medium'}
                  variant="outlined"
                  startIcon={<ChevronLeftIcon />}
                  onClick={() => onPageChange(pagination.current_page - 1)}
                  disabled={!pagination.has_previous || loading}
                  sx={{ minWidth: isDense ? 'auto' : '100px' }}
                >
                  {!isDense && 'Previous'}
                </Button>

                <Button
                  size={isDense ? 'small' : 'medium'}
                  variant="outlined"
                  endIcon={<ChevronRightIcon />}
                  onClick={() => onPageChange(pagination.current_page + 1)}
                  disabled={!pagination.has_next || loading}
                  sx={{ minWidth: isDense ? 'auto' : '100px' }}
                >
                  {!isDense && 'Next'}
                </Button>

                <Button
                  size={isDense ? 'small' : 'medium'}
                  variant="outlined"
                  endIcon={<LastPageIcon />}
                  onClick={() => onPageChange(pagination.total_pages - 1)}
                  disabled={!pagination.has_next || loading}
                  sx={{ minWidth: isDense ? 'auto' : '100px' }}
                >
                  {!isDense && 'Last'}
                </Button>
              </Stack>
            </Grid>

            {/* Page Indicator */}
            <Grid item xs={12} sm="auto" sx={{ display: 'flex', alignItems: 'center', justifyContent: { xs: 'flex-start', sm: 'flex-end' } }}>
              <Typography variant={typographyVariant} sx={{ mr: spacing }}>
                Page {pagination.current_page + 1} of {pagination.total_pages}
              </Typography>
            </Grid>
          </Grid>
        )}

        {/* Go-to-Page Control */}
        {pagination.total_pages > 1 && (
          <Grid container spacing={spacing} alignItems="center">
            <Grid item xs={12} sm="auto">
              <Stack direction="row" spacing={1} alignItems="center">
                <TextField
                  size={isDense ? 'small' : 'medium'}
                  type="number"
                  inputProps={{
                    min: 1,
                    max: pagination.total_pages,
                  }}
                  value={goToPageInput}
                  onChange={(e) => setGoToPageInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleGoToPage();
                    }
                  }}
                  placeholder="Go to page"
                  disabled={loading}
                  sx={{ width: isDense ? '80px' : '120px' }}
                />
                <Button
                  size={isDense ? 'small' : 'medium'}
                  variant="contained"
                  onClick={handleGoToPage}
                  disabled={loading || !goToPageInput}
                  sx={{ minWidth: isDense ? 'auto' : '80px' }}
                >
                  {isDense ? 'Go' : 'Go to Page'}
                </Button>
              </Stack>
            </Grid>
          </Grid>
        )}

        {/* Alternative Pagination Component (Material-UI Pagination) */}
        {pagination.total_pages > 1 && !isDense && (
          <Grid container spacing={spacing} justifyContent="center">
            <Grid item>
              <Pagination
                count={pagination.total_pages}
                page={pagination.current_page + 1}
                onChange={(event, page) => onPageChange(page - 1)}
                disabled={loading}
                size="medium"
                siblingCount={2}
                boundaryCount={1}
              />
            </Grid>
          </Grid>
        )}
      </Stack>
    </Paper>
  );
};

export default VariantPagination;
