export interface ChapterInfo {
  id: string;
  title: string;
  content_length: number;
  order: number;
}

export interface BookInfo {
  id: string;
  title: string;
  author?: string;
  language: string;
  total_chapters: number;
  chapters: ChapterInfo[];
  upload_time: string;
  file_path: string;
}

export interface TranslationTask {
  id: string;
  book_id: string;
  chapter_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface AudioTask {
  id: string;
  book_id: string;
  chapter_id: string;
  translation_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  audio_url?: string;
  duration?: number;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface PlaylistItem {
  chapter_id: string;
  chapter_title: string;
  audio_url: string;
  duration: number;
  order: number;
}

export interface BookPlaylist {
  book_id: string;
  book_title: string;
  total_duration: number;
  items: PlaylistItem[];
}