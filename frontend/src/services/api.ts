import axios from 'axios';
import { BookInfo, ChapterInfo, TranslationTask, AudioTask, BookPlaylist } from '../types/book';

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// EPUB相关API
export const epubAPI = {
  getAllBooks: async (): Promise<BookInfo[]> => {
    const response = await api.get('/epub/books');
    return response.data;
  },

  getBook: async (bookId: string): Promise<BookInfo> => {
    const response = await api.get(`/epub/books/${bookId}`);
    return response.data;
  },

  deleteBook: async (bookId: string): Promise<{ message: string; book_id: string }> => {
    const response = await api.delete(`/epub/books/${bookId}`);
    return response.data;
  },

  uploadEpub: async (file: File): Promise<BookInfo> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/epub/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  getChapters: async (bookId: string): Promise<ChapterInfo[]> => {
    const response = await api.get(`/epub/books/${bookId}/chapters`);
    return response.data;
  },

  getChapterContent: async (bookId: string, chapterId: string): Promise<string> => {
    const response = await api.get(`/epub/books/${bookId}/chapters/${chapterId}`);
    return response.data.content;
  },
};

// 翻译相关API
export const translationAPI = {
  translateText: async (text: string, model?: string) => {
    const response = await api.post('/translation/translate', {
      text,
      model: model || 'gpt-3.5-turbo'
    });
    return response.data;
  },

  translateChapter: async (bookId: string, chapterId: string): Promise<string> => {
    const response = await api.post(`/translation/translate/chapter`, null, {
      params: { book_id: bookId, chapter_id: chapterId }
    });
    return response.data.translation_id;
  },

  getTranslationStatus: async (translationId: string): Promise<TranslationTask> => {
    const response = await api.get(`/translation/translation/${translationId}`);
    return response.data;
  },

  getChapterTranslation: async (bookId: string, chapterId: string): Promise<string> => {
    const response = await api.get(`/translation/books/${bookId}/chapters/${chapterId}/translation`);
    return response.data.translation;
  },
};

// TTS相关API
export const ttsAPI = {
  generateSpeech: async (text: string, voice?: string, speed?: number, refAudioUrl?: string, refText?: string) => {
    const requestData: any = {
      text,
      voice: voice || 'zh-CN-XiaoxiaoNeural',
      speed: speed || 1.0
    };
    
    if (refAudioUrl) {
      requestData.ref_audio_url = refAudioUrl;
    }
    if (refText !== undefined) {
      requestData.ref_text = refText;
    }
    
    const response = await api.post('/tts/generate', requestData);
    return response.data;
  },

  uploadReferenceAudio: async (file: File): Promise<{file_id: string, file_path: string}> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // 直接调用F5-TTS服务的上传接口
    const response = await axios.post('http://localhost:8001/upload-ref-audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  generateChapterAudio: async (
    bookId: string, 
    chapterId: string, 
    translationId?: string
  ): Promise<string> => {
    const params: any = { 
      book_id: bookId, 
      chapter_id: chapterId
    };
    
    if (translationId) {
      params.translation_id = translationId;
    }
    
    const response = await api.post(`/tts/generate/chapter`, null, {
      params
    });
    return response.data.audio_id;
  },

  getAudioStatus: async (audioId: string): Promise<AudioTask> => {
    const response = await api.get(`/tts/audio/${audioId}/status`);
    return response.data;
  },

  getChapterAudioInfo: async (bookId: string, chapterId: string) => {
    const response = await api.get(`/tts/books/${bookId}/chapters/${chapterId}/audio`);
    return response.data;
  },
};

// 音频相关API
export const audioAPI = {
  mergeBookAudio: async (bookId: string, chapterIds: string[]) => {
    const response = await api.post(`/audio/merge/book`, null, {
      params: { book_id: bookId },
      data: { chapter_ids: chapterIds }
    });
    return response.data;
  },

  getBookPlaylist: async (bookId: string): Promise<BookPlaylist> => {
    const response = await api.get(`/audio/books/${bookId}/playlist`);
    return response.data.playlist;
  },

  downloadAudio: async (audioFile: string): Promise<Blob> => {
    const response = await api.get(`/audio/download/${audioFile}`, {
      responseType: 'blob'
    });
    return response.data;
  },
};

export default api;

// 导出便捷函数
export const getAllBooks = epubAPI.getAllBooks;