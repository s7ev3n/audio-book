import { create } from 'zustand';
import { BookInfo, ChapterInfo } from '../types/book';

interface BookState {
  currentBook: BookInfo | null;
  chapters: ChapterInfo[];
  currentChapter: ChapterInfo | null;
  currentChapterIndex: number;
  originalText: string;
  translatedText: string;
  isTranslating: boolean;
  isGeneratingAudio: boolean;
  audioUrl: string | null;
  
  // Actions
  setCurrentBook: (book: BookInfo) => void;
  setChapters: (chapters: ChapterInfo[]) => void;
  setCurrentChapter: (chapter: ChapterInfo, index: number) => void;
  setOriginalText: (text: string) => void;
  setTranslatedText: (text: string) => void;
  setTranslating: (isTranslating: boolean) => void;
  setGeneratingAudio: (isGenerating: boolean) => void;
  setAudioUrl: (url: string | null) => void;
  clearBook: () => void;
}

export const useBookStore = create<BookState>((set, get) => ({
  currentBook: null,
  chapters: [],
  currentChapter: null,
  currentChapterIndex: 0,
  originalText: '',
  translatedText: '',
  isTranslating: false,
  isGeneratingAudio: false,
  audioUrl: null,

  setCurrentBook: (book) => set({ currentBook: book }),
  
  setChapters: (chapters) => set({ chapters }),
  
  setCurrentChapter: (chapter, index) => set({ 
    currentChapter: chapter, 
    currentChapterIndex: index,
    originalText: '',
    translatedText: '',
    audioUrl: null
  }),
  
  setOriginalText: (text) => set({ originalText: text }),
  
  setTranslatedText: (text) => set({ translatedText: text }),
  
  setTranslating: (isTranslating) => set({ isTranslating }),
  
  setGeneratingAudio: (isGenerating) => set({ isGeneratingAudio: isGenerating }),
  
  setAudioUrl: (url) => set({ audioUrl: url }),
  
  clearBook: () => set({
    currentBook: null,
    chapters: [],
    currentChapter: null,
    currentChapterIndex: 0,
    originalText: '',
    translatedText: '',
    isTranslating: false,
    isGeneratingAudio: false,
    audioUrl: null
  })
}));