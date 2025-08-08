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
  generateSpeech: async (text: string, voice?: string, speed?: number) => {
    const response = await api.post('/tts/generate', {
      text,
      voice: voice || 'zh-CN-XiaoxiaoNeural',
      speed: speed || 1.0
    });
    return response.data;
  },

  generateChapterAudio: async (
    bookId: string, 
    chapterId: string, 
    translationId: string
  ): Promise<string> => {
    const response = await api.post(`/tts/generate/chapter`, null, {
      params: { 
        book_id: bookId, 
        chapter_id: chapterId, 
        translation_id: translationId 
      }
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