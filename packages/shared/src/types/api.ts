/**
 * Standard shape for all paginated list endpoints.
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total_count: number;
    has_more: boolean;
    next_cursor?: string | null;
  };
}

/**
 * Standard shape for application API errors.
 */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}
