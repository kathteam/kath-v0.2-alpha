/**
 * Pagination API Utilities
 *
 * Helper functions for making paginated API requests to the backend.
 * Handles constructing URLs, managing parameters, and caching.
 */

export interface PaginatedResponse {
  page: number;
  totalRows: number;
  header: string[];
  rows: (string | number | null)[][];
  pagination: {
    current_page: number;
    page_size: number;
    total_entries: number;
    total_pages: number;
    has_previous: boolean;
    has_next: boolean;
    showing_from: number;
    showing_to: number;
  };
}

export interface FilterSpec {
  [columnName: string]: {
    operator: string;
    value: string | number;
  };
}

export interface SortSpec {
  [columnName: string]: 'asc' | 'desc';
}

/**
 * Fetch paginated variant data from the backend.
 *
 * @param filePath - File path within workspace
 * @param page - Page number (0-indexed)
 * @param pageSize - Number of rows per page
 * @param filters - Optional filter specifications
 * @param sorts - Optional sort specifications
 * @param uuid - Workspace UUID from headers
 * @param sid - Session ID from headers
 * @returns Promise with paginated response
 */
export async function fetchPaginatedVariants(
  filePath: string,
  page: number = 0,
  pageSize: number = 25,
  filters?: FilterSpec,
  sorts?: SortSpec,
  uuid?: string,
  sid?: string
): Promise<PaginatedResponse> {
  // Build query parameters
  const params = new URLSearchParams();
  params.append('page', page.toString());
  params.append('rowsPerPage', pageSize.toString());

  if (filters && Object.keys(filters).length > 0) {
    params.append('filters', JSON.stringify(filters));
  }

  if (sorts && Object.keys(sorts).length > 0) {
    params.append('sorts', JSON.stringify(sorts));
  }

  // Build headers
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (uuid) {
    headers['uuid'] = uuid;
  }

  if (sid) {
    headers['sid'] = sid;
  }

  // Construct URL
  const encodedPath = encodeURIComponent(filePath);
  const url = `/api/v1/workspace/file/${encodedPath}?${params.toString()}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(
        `Failed to fetch variants: ${response.status} ${response.statusText}`
      );
    }

    const data: PaginatedResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching paginated variants:', error);
    throw error;
  }
}

/**
 * Build a filter specification for a single column.
 *
 * @param columnName - Column to filter
 * @param operator - Filter operator (contains, equals, gt, etc.)
 * @param value - Filter value
 * @returns Filter specification object
 */
export function buildFilter(
  columnName: string,
  operator: string,
  value: string | number
): FilterSpec {
  return {
    [columnName]: {
      operator,
      value,
    },
  };
}

/**
 * Build a sort specification for a single column.
 *
 * @param columnName - Column to sort
 * @param order - Sort order (asc or desc)
 * @returns Sort specification object
 */
export function buildSort(
  columnName: string,
  order: 'asc' | 'desc' = 'asc'
): SortSpec {
  return {
    [columnName]: order,
  };
}

/**
 * Merge multiple filter specifications.
 *
 * @param filters - Array of filter specs to merge
 * @returns Combined filter specification
 */
export function mergeFilters(...filters: FilterSpec[]): FilterSpec {
  return filters.reduce((acc, filter) => ({ ...acc, ...filter }), {});
}

/**
 * Calculate total pages needed for a given total rows and page size.
 *
 * @param totalRows - Total number of rows
 * @param pageSize - Rows per page
 * @returns Total number of pages
 */
export function calculateTotalPages(totalRows: number, pageSize: number): number {
  return Math.ceil(totalRows / pageSize);
}

/**
 * Validate page number is within valid range.
 *
 * @param page - Current page (0-indexed)
 * @param totalPages - Total pages available
 * @returns True if page is valid
 */
export function isValidPage(page: number, totalPages: number): boolean {
  return page >= 0 && page < totalPages;
}

/**
 * Get previous page number (with bounds checking).
 *
 * @param currentPage - Current page (0-indexed)
 * @returns Previous page number, or current page if at first page
 */
export function getPreviousPage(currentPage: number): number {
  return Math.max(0, currentPage - 1);
}

/**
 * Get next page number (with bounds checking).
 *
 * @param currentPage - Current page (0-indexed)
 * @param totalPages - Total pages available
 * @returns Next page number, or current page if at last page
 */
export function getNextPage(currentPage: number, totalPages: number): number {
  return Math.min(currentPage + 1, totalPages - 1);
}

/**
 * Cache for storing previously fetched paginated responses.
 * Helps prevent redundant API calls.
 */
export class PaginationCache {
  private cache: Map<
    string,
    { data: PaginatedResponse; timestamp: number }
  > = new Map();

  private ttl: number = 5 * 60 * 1000; // 5 minutes default TTL

  /**
   * Create a cache key from fetch parameters.
   *
   * @param filePath - File path
   * @param page - Page number
   * @param pageSize - Page size
   * @returns Cache key string
   */
  private getCacheKey(filePath: string, page: number, pageSize: number): string {
    return `${filePath}_p${page}_s${pageSize}`;
  }

  /**
   * Get cached data if valid.
   *
   * @param filePath - File path
   * @param page - Page number
   * @param pageSize - Page size
   * @returns Cached response or undefined
   */
  get(filePath: string, page: number, pageSize: number): PaginatedResponse | undefined {
    const key = this.getCacheKey(filePath, page, pageSize);
    const cached = this.cache.get(key);

    if (!cached) {
      return undefined;
    }

    // Check if cache is still valid
    const age = Date.now() - cached.timestamp;
    if (age > this.ttl) {
      this.cache.delete(key);
      return undefined;
    }

    return cached.data;
  }

  /**
   * Set cached data.
   *
   * @param filePath - File path
   * @param page - Page number
   * @param pageSize - Page size
   * @param data - Response data to cache
   */
  set(
    filePath: string,
    page: number,
    pageSize: number,
    data: PaginatedResponse
  ): void {
    const key = this.getCacheKey(filePath, page, pageSize);
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  /**
   * Clear all cached data for a file.
   *
   * @param filePath - File path to clear cache for
   */
  clearForFile(filePath: string): void {
    const keysToDelete: string[] = [];
    for (const key of this.cache.keys()) {
      if (key.startsWith(filePath)) {
        keysToDelete.push(key);
      }
    }
    keysToDelete.forEach((key) => this.cache.delete(key));
  }

  /**
   * Clear entire cache.
   */
  clearAll(): void {
    this.cache.clear();
  }

  /**
   * Set cache TTL.
   *
   * @param ttlMs - Time to live in milliseconds
   */
  setTTL(ttlMs: number): void {
    this.ttl = ttlMs;
  }
}

// Global cache instance
export const paginationCache = new PaginationCache();
