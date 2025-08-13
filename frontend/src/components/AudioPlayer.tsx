import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Slider,
  Stack,
  Tooltip
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  SkipPrevious,
  SkipNext,
  VolumeUp,
  VolumeOff
} from '@mui/icons-material';

import { ChapterInfo } from '../types/book';

interface AudioPlayerProps {
  bookId: string;
  chapter: ChapterInfo | null;
  chapters: ChapterInfo[];
  currentIndex: number;
  onChapterChange: (chapter: ChapterInfo, index: number) => void;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({
  bookId,
  chapter,
  chapters,
  currentIndex,
  onChapterChange
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // 当章节变化时，更新音频URL
  useEffect(() => {
    if (chapter && bookId) {
      // 与后端保持一致的文件名转换逻辑
      const safeChapterId = chapter.id.replace(/\//g, "_").replace(/\\/g, "_").replace(/:/g, "_");
      const newAudioUrl = `/storage/audio/${bookId}_${safeChapterId}.mp3`;
      setAudioUrl(newAudioUrl);
      setCurrentTime(0);
      setIsPlaying(false);
    }
  }, [chapter, bookId]);

  // 音频事件处理
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleDurationChange = () => {
      setDuration(audio.duration || 0);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      // 自动播放下一章节
      if (currentIndex < chapters.length - 1) {
        const nextChapter = chapters[currentIndex + 1];
        onChapterChange(nextChapter, currentIndex + 1);
      }
    };

    const handleLoadStart = () => {
      setCurrentTime(0);
      setDuration(0);
    };

    const handleError = (e: Event) => {
      console.error('Audio loading error:', e);
      console.error('Audio source:', audio.src);
      console.error('Audio network state:', audio.networkState);
      console.error('Audio ready state:', audio.readyState);
    };

    const handleCanPlay = () => {
      console.log('Audio can play:', audio.src);
      console.log('Audio duration:', audio.duration);
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('durationchange', handleDurationChange);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('error', handleError);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('durationchange', handleDurationChange);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [chapters, currentIndex, onChapterChange]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    console.log('togglePlayPause called');
    console.log('audio:', audio);
    console.log('audioUrl:', audioUrl);
    console.log('isPlaying:', isPlaying);
    
    if (!audio || !audioUrl) {
      console.log('No audio element or URL available');
      return;
    }

    if (isPlaying) {
      audio.pause();
    } else {
      console.log('Attempting to play audio from:', audioUrl);
      audio.play().catch(error => {
        console.error('Audio play failed:', error);
      });
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (event: Event, newValue: number | number[]) => {
    const audio = audioRef.current;
    if (!audio) return;

    const seekTime = newValue as number;
    audio.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const handleVolumeChange = (event: Event, newValue: number | number[]) => {
    const audio = audioRef.current;
    if (!audio) return;

    const newVolume = (newValue as number) / 100;
    audio.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isMuted) {
      audio.volume = volume;
      setIsMuted(false);
    } else {
      audio.volume = 0;
      setIsMuted(true);
    }
  };

  const playPrevious = () => {
    if (currentIndex > 0) {
      const prevChapter = chapters[currentIndex - 1];
      onChapterChange(prevChapter, currentIndex - 1);
    }
  };

  const playNext = () => {
    if (currentIndex < chapters.length - 1) {
      const nextChapter = chapters[currentIndex + 1];
      onChapterChange(nextChapter, currentIndex + 1);
    }
  };

  const formatTime = (time: number): string => {
    if (isNaN(time)) return '0:00';
    
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (!chapter) {
    return (
      <Paper elevation={3} sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary" align="center">
          请选择章节开始播放
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          preload="metadata"
        />
      )}

      {/* 章节信息 */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" noWrap>
          {chapter.title}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          第 {currentIndex + 1} 章 / 共 {chapters.length} 章
        </Typography>
      </Box>

      {/* 进度条 */}
      <Box sx={{ mb: 2 }}>
        <Slider
          value={currentTime}
          max={duration || 100}
          onChange={handleSeek}
          size="small"
          sx={{ mb: 1 }}
          disabled={!audioUrl || duration === 0}
        />
        
        <Stack direction="row" justifyContent="space-between">
          <Typography variant="caption" color="text.secondary">
            {formatTime(currentTime)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {formatTime(duration)}
          </Typography>
        </Stack>
      </Box>

      {/* 控制按钮 */}
      <Stack direction="row" alignItems="center" justifyContent="center" spacing={1}>
        {/* 上一章 */}
        <Tooltip title="上一章">
          <span>
            <IconButton 
              onClick={playPrevious} 
              disabled={currentIndex === 0}
            >
              <SkipPrevious />
            </IconButton>
          </span>
        </Tooltip>

        {/* 播放/暂停 */}
        <Tooltip title={isPlaying ? "暂停" : "播放"}>
          <span>
            <IconButton 
              onClick={togglePlayPause} 
              size="large"
              disabled={!audioUrl}
              sx={{ 
                bgcolor: 'primary.main', 
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                '&:disabled': { bgcolor: 'action.disabled' }
              }}
            >
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
          </span>
        </Tooltip>

        {/* 下一章 */}
        <Tooltip title="下一章">
          <span>
            <IconButton 
              onClick={playNext} 
              disabled={currentIndex === chapters.length - 1}
            >
              <SkipNext />
            </IconButton>
          </span>
        </Tooltip>

        {/* 音量控制 */}
        <Box sx={{ display: 'flex', alignItems: 'center', ml: 2, minWidth: 120 }}>
          <Tooltip title={isMuted ? "取消静音" : "静音"}>
            <IconButton onClick={toggleMute} size="small">
              {isMuted ? <VolumeOff /> : <VolumeUp />}
            </IconButton>
          </Tooltip>
          
          <Slider
            value={isMuted ? 0 : volume * 100}
            onChange={handleVolumeChange}
            size="small"
            max={100}
            sx={{ ml: 1, width: 80 }}
          />
        </Box>
      </Stack>

      {/* 音频不存在提示 */}
      {!audioUrl && (
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            该章节音频尚未生成，请先翻译并生成语音
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default AudioPlayer;