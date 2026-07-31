export type RequestLog = {
  id: number;
  request_id: string | null;
  user_id: string | null;
  prompt: string | null;
  response: string | null;
  threat_type: string | null;
  layer: number | null;
  flagged: boolean;
  timestamp: string | null;
  ip_address: string | null;
  latency_ms: number | null;
};

export type LogsResponse = {
  logs: RequestLog[];
  total: number;
  page: number;
  limit: number;
  pages: number;
};
