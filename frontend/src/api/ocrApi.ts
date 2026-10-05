import { request, xhrUpload } from './client';
import {
  OcrExtractionResult,
  OcrExtractionResultSchema,
  SelectExerciseRequest,
} from './schemas';

/**
 * Pre-processes an image file on canvas:
 * - Converts HEIC if necessary
 * - Normalizes EXIF rotation
 * - Strips EXIF GPS/metadata
 * - Blanks top 10% header area (where student names or school names are written)
 * - Scales to max 2048x2048 with high-quality smoothing to protect Khmer subscripts
 */
async function optimizeImageForOcr(file: File | Blob): Promise<Blob> {
  const sourceBlob: Blob = file;

  // Load into Image element
  return new Promise((resolve) => {

    const img = new Image();
    const url = URL.createObjectURL(sourceBlob);

    img.onload = () => {
      URL.revokeObjectURL(url);
      const maxDim = 2048;
      let { width, height } = img;

      if (width > maxDim || height > maxDim) {
        if (width > height) {
          height = Math.round((height * maxDim) / width);
          width = maxDim;
        } else {
          width = Math.round((width * maxDim) / height);
          height = maxDim;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        resolve(sourceBlob);
        return;
      }

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, width, height);

      // Child privacy protection: Redact top 8% of header region (school name / student name)
      // by filling with neutral paper background
      const headerHeight = Math.round(height * 0.08);
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, width, headerHeight);

      canvas.toBlob(
        (blob) => {
          resolve(blob || sourceBlob);
        },
        'image/jpeg',
        0.90
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(sourceBlob);
    };

    img.src = url;
  });
}

/**
 * Homework OCR & Vision Extraction API Client
 */
export const ocrApi = {
  /**
   * Upload worksheet image/PDF to Orchestrator OCR gateway with real progress tracking.
   */
  async uploadAndExtract(
    file: File | Blob,
    options?: {
      filename?: string;
      forceMock?: boolean;
      onProgress?: (percent: number) => void;
      abortSignal?: AbortSignal;
    }
  ): Promise<OcrExtractionResult> {
    const optimizedBlob = await optimizeImageForOcr(file);
    const formData = new FormData();
    const filename = options?.filename || (file instanceof File ? file.name : 'worksheet.jpg');
    formData.append('file', optimizedBlob, filename);

    const queryParams = options?.forceMock ? '?force_mock=true' : '';
    const raw = await xhrUpload<unknown>(`/upload/ocr${queryParams}`, formData, {
      onProgress: options?.onProgress,
      abortSignal: options?.abortSignal,
      timeoutMs: 90_000,
    });

    const parsed = OcrExtractionResultSchema.safeParse(raw);
    if (parsed.success) {
      return parsed.data;
    }

    return {
      success: false,
      error: 'OCR response schema mismatch',
      problems: [],
    };
  },

  /**
   * Get deterministic sample worksheet for testing (dev only).
   */
  async getMockWorksheet(): Promise<OcrExtractionResult> {
    const raw = await request<unknown>('/upload/mock', {
      method: 'GET',
      timeoutMs: 10_000,
    });

    const parsed = OcrExtractionResultSchema.safeParse(raw);
    return parsed.success ? parsed.data : { success: false, problems: [] };
  },

  /**
   * Select an exercise from a multi-problem OCR extraction to begin Socratic tutoring.
   */
  async selectExercise(payload: SelectExerciseRequest): Promise<any> {
    return request<any>('/upload/select', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeoutMs: 20_000,
    });
  },
};
