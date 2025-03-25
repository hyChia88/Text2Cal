export interface Log {
  id: string;
  content: string;
}

export interface ApiResponse<T> {
  status: string;
  data?: T;
  error?: string;
}