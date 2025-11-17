import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

export interface UploadResponse {
  job_id: string;
  message: string;
  status: string;
}

export interface StatusResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  message: string;
  error?: string;
}

export interface ModelPredictions {
  [key: string]: {
    fake: number;
    real: number;
  };
}

export interface ResultsResponse {
  job_id: string;
  status: string;
  verdict: string;  // "Fake" from backend
  confidence: number;
  probability: number;  // Single probability from backend
  processing_time_seconds: number;
  filename: string;
  file_size_mb: number;
  upload_timestamp: string;
  completion_timestamp: string;
  gradcam_avg_heatmap: string;
  gradcam_dir: string;
  gradcam_enabled: boolean;
  gradcam_frame_count: number;
  threshold: number;
  error_message: string | null;
}

// ADD THIS INTERFACE (after ResultsResponse, before api object)
export interface JobSummary {
  job_id: string;
  filename: string;
  verdict: string;
  confidence: number;
  upload_timestamp: string;
  status: string;
  file_size_mb: number;
}

export interface JobsListResponse {
  jobs: JobSummary[];
  count: number;
  limit: number;
  offset: number;
}

// Then update getAllJobs to use the interface:
getAllJobs: async (limit: number = 50, offset: number = 0): Promise<JobsListResponse> => {
  const response = await axios.get(`${API_BASE_URL}/jobs`, {
    params: { limit, offset }
  });
  return response.data;
}


// Model name mapping for display
export const MODEL_NAME_MAP: { [key: string]: string } = {
  efficientnet: 'EfficientNet-B4',
  inceptionv3: 'InceptionV3',
  resnet50: 'ResNet-50',
  xception: 'Xception',
};

export const api = {
  uploadVideo: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('video', file);
    
    const response = await axios.post<UploadResponse>(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  getStatus: async (jobId: string): Promise<StatusResponse> => {
    const response = await axios.get<StatusResponse>(`${API_BASE_URL}/status/${jobId}`);
    return response.data;
  },

  getResults: async (jobId: string): Promise<ResultsResponse> => {
    const response = await axios.get<ResultsResponse>(`${API_BASE_URL}/results/${jobId}`);
    return response.data;
  },

  getGradCamUrl: (jobId: string, filename: string): string => {
    return `${API_BASE_URL}/gradcam/${jobId}/${filename}`;
  },

  getAllJobs: async (limit: number = 50, offset: number = 0): Promise<JobsListResponse> => {
    const response = await axios.get(`${API_BASE_URL}/jobs`, {
      params: { limit, offset }
    });
    return response.data;
  }
};
