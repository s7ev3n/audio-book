import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Translate,
  VolumeUp,
  Refresh,
  PlayArrow
} from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';

import { ChapterInfo } from '../types/book';
import { epubAPI, translationAPI, ttsAPI } from '../services/api';
import { useBookStore } from '../store/bookStore';

interface TextDisplayProps {
  bookId: string;
  chapter: ChapterInfo;
}

const TextDisplay: React.FC<TextDisplayProps> = ({ bookId, chapter }) => {
  const {
    originalText,
    translatedText,
    isTranslating,
    isGeneratingAudio,
    setOriginalText,
    setTranslatedText,
    setTranslating,
    setGeneratingAudio,
    setAudioUrl
  } = useBookStore();

  const [translationTaskId, setTranslationTaskId] = useState<string | null>(null);
  const [audioTaskId, setAudioTaskId] = useState<string | null>(null);
  const [highlightedText, setHighlightedText] = useState<string>('');

  // 获取原文内容
  const { data: chapterContent, isLoading } = useQuery(
    ['chapterContent', bookId, chapter.id],
    () => epubAPI.getChapterContent(bookId, chapter.id),
    {
      onSuccess: (content) => {
        setOriginalText(content);
      }
    }
  );

  // 翻译章节
  const translateMutation = useMutation(
    () => translationAPI.translateChapter(bookId, chapter.id),
    {
      onSuccess: (taskId) => {
        setTranslationTaskId(taskId);
        setTranslating(true);
      },
      onError: (error) => {
        console.error('Translation failed:', error);
        setTranslating(false);
      }
    }
  );

  // 生成音频
  const generateAudioMutation = useMutation(
    (translationId: string) => 
      ttsAPI.generateChapterAudio(bookId, chapter.id, translationId),
    {
      onSuccess: (taskId) => {
        setAudioTaskId(taskId);
        setGeneratingAudio(true);
      },
      onError: (error) => {
        console.error('Audio generation failed:', error);
        setGeneratingAudio(false);
      }
    }
  );

  // 轮询翻译状态
  useQuery(
    ['translationStatus', translationTaskId],
    () => translationAPI.getTranslationStatus(translationTaskId!),
    {
      enabled: !!translationTaskId && isTranslating,
      refetchInterval: 2000,
      onSuccess: (status) => {
        if (status.status === 'completed') {
          // 这里应该获取翻译结果，简化处理
          setTranslatedText('翻译已完成，请刷新查看结果'); // 实际应该调用API获取结果
          setTranslating(false);
          setTranslationTaskId(null);
        } else if (status.status === 'failed') {
          setTranslating(false);
          setTranslationTaskId(null);
        }
      }
    }
  );

  // 轮询音频生成状态
  useQuery(
    ['audioStatus', audioTaskId],
    () => ttsAPI.getAudioStatus(audioTaskId!),
    {
      enabled: !!audioTaskId && isGeneratingAudio,
      refetchInterval: 3000,
      onSuccess: (status) => {
        if (status.status === 'completed' && status.audio_url) {
          setAudioUrl(status.audio_url);
          setGeneratingAudio(false);
          setAudioTaskId(null);
        } else if (status.status === 'failed') {
          setGeneratingAudio(false);
          setAudioTaskId(null);
        }
      }
    }
  );

  const handleTranslate = () => {
    if (!isTranslating) {
      translateMutation.mutate();
    }
  };

  const handleGenerateAudio = () => {
    if (translationTaskId && !isGeneratingAudio) {
      generateAudioMutation.mutate(translationTaskId);
    }
  };

  const highlightTextSegment = (text: string, highlight: string) => {
    if (!highlight) return text;
    
    const parts = text.split(new RegExp(`(${highlight})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === highlight.toLowerCase() ? (
        <span key={index} style={{ 
          backgroundColor: '#ffeb3b', 
          padding: '2px 4px',
          borderRadius: '4px' 
        }}>
          {part}
        </span>
      ) : part
    );
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
      {/* 章节标题和操作按钮 */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="h2">
            {chapter.title}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="翻译章节">
              <Button
                variant="outlined"
                startIcon={isTranslating ? <CircularProgress size={16} /> : <Translate />}
                onClick={handleTranslate}
                disabled={isTranslating}
                size="small"
              >
                {isTranslating ? '翻译中...' : '翻译'}
              </Button>
            </Tooltip>
            
            <Tooltip title="生成语音">
              <Button
                variant="outlined"
                startIcon={isGeneratingAudio ? <CircularProgress size={16} /> : <VolumeUp />}
                onClick={handleGenerateAudio}
                disabled={!translatedText || isGeneratingAudio}
                size="small"
              >
                {isGeneratingAudio ? '生成中...' : '生成语音'}
              </Button>
            </Tooltip>
          </Box>
        </Box>
        
        {translateMutation.isError && (
          <Alert severity="error" sx={{ mb: 1 }}>
            翻译失败，请重试
          </Alert>
        )}
        
        {generateAudioMutation.isError && (
          <Alert severity="error" sx={{ mb: 1 }}>
            音频生成失败，请重试
          </Alert>
        )}
      </Paper>

      {/* 双栏文本显示 */}
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <Grid container spacing={2} sx={{ height: '100%' }}>
          {/* 原文栏 */}
          <Grid item xs={12} md={6} sx={{ height: '100%' }}>
            <Paper 
              elevation={2} 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                overflow: 'hidden'
              }}
            >
              <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  🇺🇸 原文 (English)
                </Typography>
              </Box>
              
              <Box sx={{ 
                flexGrow: 1, 
                p: 2, 
                overflow: 'auto',
                fontSize: '0.95rem',
                lineHeight: 1.6
              }}>
                <Typography 
                  variant="body1" 
                  component="div"
                  sx={{ whiteSpace: 'pre-wrap' }}
                >
                  {highlightTextSegment(originalText, highlightedText)}
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* 译文栏 */}
          <Grid item xs={12} md={6} sx={{ height: '100%' }}>
            <Paper 
              elevation={2} 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                overflow: 'hidden'
              }}
            >
              <Box sx={{ p: 2, bgcolor: 'secondary.main', color: 'secondary.contrastText' }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  🇨🇳 译文 (中文)
                </Typography>
              </Box>
              
              <Box sx={{ 
                flexGrow: 1, 
                p: 2, 
                overflow: 'auto',
                fontSize: '1rem',
                lineHeight: 1.8
              }}>
                {translatedText ? (
                  <Typography 
                    variant="body1" 
                    component="div"
                    sx={{ whiteSpace: 'pre-wrap' }}
                  >
                    {highlightTextSegment(translatedText, highlightedText)}
                  </Typography>
                ) : (
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center',
                    height: '100%',
                    color: 'text.secondary'
                  }}>
                    <Translate sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                    <Typography variant="body1" align="center">
                      点击上方"翻译"按钮开始翻译章节
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default TextDisplay;