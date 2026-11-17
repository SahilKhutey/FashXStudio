import {
  validateLocalPhoto,
  executePhotoUploadPipeline,
  MIN_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_BYTES,
} from '../src/features/media/services/uploadService';
import { mediaApi } from '../src/features/media/services/mediaApi';
import { SelectedPhoto } from '../src/features/media/types/media.types';

jest.mock('../src/features/media/services/mediaApi', () => ({
  mediaApi: {
    initiateUpload: jest.fn(),
    completeUpload: jest.fn(),
    getUploadStatus: jest.fn(),
    getMediaMetadata: jest.fn(),
    getMediaAccessUrl: jest.fn(),
    deleteMedia: jest.fn(),
  },
}));

describe('Photo Upload Mobile Pipeline', () => {
  const validPhoto: SelectedPhoto = {
    uri: 'file:///path/to/valid_image.jpg',
    filename: 'valid_image.jpg',
    contentType: 'image/jpeg',
    fileSizeBytes: 500 * 1024, // 500 KB
    width: 1200,
    height: 1600,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (init?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          status: 200,
        });
      }
      return Promise.resolve({
        ok: true,
        blob: () => Promise.resolve(new Blob(['fake-image-bytes'], { type: 'image/jpeg' })),
      });
    }) as jest.Mock;
  });

  describe('validateLocalPhoto', () => {
    it('accepts valid JPEG within constraints', () => {
      const res = validateLocalPhoto(validPhoto);
      expect(res.valid).toBe(true);
      expect(res.errors).toHaveLength(0);
    });

    it('accepts valid PNG and WebP within constraints', () => {
      expect(validateLocalPhoto({ ...validPhoto, contentType: 'image/png' }).valid).toBe(true);
      expect(validateLocalPhoto({ ...validPhoto, contentType: 'image/webp' }).valid).toBe(true);
    });

    it('rejects unsupported MIME types like GIF or SVG', () => {
      const gifRes = validateLocalPhoto({ ...validPhoto, contentType: 'image/gif' });
      expect(gifRes.valid).toBe(false);
      expect(gifRes.errors[0]).toMatch(/Supported formats are JPEG, PNG, and WebP/);

      const svgRes = validateLocalPhoto({ ...validPhoto, contentType: 'image/svg+xml' });
      expect(svgRes.valid).toBe(false);
    });

    it('rejects files below minimum 10 KB threshold', () => {
      const smallRes = validateLocalPhoto({
        ...validPhoto,
        fileSizeBytes: MIN_FILE_SIZE_BYTES - 1,
      });
      expect(smallRes.valid).toBe(false);
      expect(smallRes.errors[0]).toMatch(/below the minimum limit/);
    });

    it('rejects files above maximum 10 MB threshold', () => {
      const largeRes = validateLocalPhoto({
        ...validPhoto,
        fileSizeBytes: MAX_FILE_SIZE_BYTES + 1,
      });
      expect(largeRes.valid).toBe(false);
      expect(largeRes.errors[0]).toMatch(/exceeds the maximum limit/);
    });

    it('rejects images exceeding 4096 px dimension', () => {
      const wideRes = validateLocalPhoto({ ...validPhoto, width: 4097, height: 2000 });
      expect(wideRes.valid).toBe(false);
      expect(wideRes.errors[0]).toMatch(/exceed the maximum limit of 4096px/);
    });

    it('rejects images exceeding 20 megapixel safety limit', () => {
      const hugeRes = validateLocalPhoto({ ...validPhoto, width: 4096, height: 5000 });
      expect(hugeRes.valid).toBe(false);
      expect(hugeRes.errors).toEqual(
        expect.arrayContaining([expect.stringMatching(/20 megapixel/)]),
      );
    });
  });

  describe('executePhotoUploadPipeline', () => {
    it('executes full upload flow: initiate -> PUT -> complete', async () => {
      (mediaApi.initiateUpload as jest.Mock).mockResolvedValueOnce({
        upload_id: 'upload-uuid-123',
        image_id: 'image-uuid-456',
        upload_url: 'https://storage.fashx.com/quarantine/upload.jpg',
        method: 'PUT',
        required_headers: { 'Content-Type': 'image/jpeg' },
        expires_in_seconds: 300,
        status: 'PENDING_UPLOAD',
      });

      (mediaApi.completeUpload as jest.Mock).mockResolvedValueOnce({
        upload_id: 'upload-uuid-123',
        image_id: 'image-uuid-456',
        status: 'AVAILABLE',
        message: 'Your photo has been validated and is available.',
      });

      const stages: string[] = [];
      const res = await executePhotoUploadPipeline(
        validPhoto,
        'VTO_PERSONAL_PHOTO',
        (s) => stages.push(s),
      );

      expect(res.status).toBe('AVAILABLE');
      expect(stages).toEqual(['initiating', 'uploading', 'validating', 'completed']);
      expect(mediaApi.initiateUpload).toHaveBeenCalledWith({
        purpose: 'VTO_PERSONAL_PHOTO',
        filename: validPhoto.filename,
        content_type: validPhoto.contentType,
        declared_size_bytes: validPhoto.fileSizeBytes,
      });
      expect(mediaApi.completeUpload).toHaveBeenCalledWith('upload-uuid-123');
    });

    it('aborts early if local pre-validation fails without calling API', async () => {
      const invalidPhoto = { ...validPhoto, fileSizeBytes: 500 }; // 500 bytes < 10KB
      await expect(executePhotoUploadPipeline(invalidPhoto, 'VTO_PERSONAL_PHOTO')).rejects.toThrow(
        /below the minimum limit/,
      );
      expect(mediaApi.initiateUpload).not.toHaveBeenCalled();
    });
  });
});
