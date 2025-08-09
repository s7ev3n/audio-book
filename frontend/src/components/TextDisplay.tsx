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
  const { data: chapterContent, isLoading, refetch } = useQuery(
    ['chapterContent', bookId, chapter.id],
    () => epubAPI.getChapterContent(bookId, chapter.id),
    {
      onSuccess: (content) => {
        setOriginalText(content);
      },
      // 确保每次章节变化都能获取到内容
      staleTime: 0, // 立即过期，确保每次都检查
      cacheTime: 5 * 60 * 1000, // 缓存5分钟
      refetchOnMount: true, // 组件挂载时重新获取
    }
  );

  // 当章节变化时，如果当前没有文本内容，则重新获取
  useEffect(() => {
    if (!originalText && chapter.id) {
      refetch();
    }
  }, [chapter.id, originalText, refetch]);

  // 检查并加载已存在的翻译内容
  useEffect(() => {
    if (chapter.id && bookId && !translatedText && !isTranslating) {
      console.log('检查是否存在翻译内容:', bookId, chapter.id);
      translationAPI.getChapterTranslation(bookId, chapter.id)
        .then((translation) => {
          console.log('找到已存在的翻译内容:', translation);
          setTranslatedText(translation);
        })
        .catch((error) => {
          console.log('未找到翻译内容或获取失败:', error.response?.status, error.message);
        });
    }
  }, [chapter.id, bookId, translatedText, isTranslating, setTranslatedText]);

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
        console.log('翻译状态更新:', status);
        if (status.status === 'completed') {
          // 翻译完成，获取翻译内容
          translationAPI.getChapterTranslation(bookId, chapter.id)
            .then((translation) => {
              console.log('获取到翻译内容:', translation);
              setTranslatedText(translation);
              setTranslating(false);
              setTranslationTaskId(null);
            })
            .catch((error) => {
              console.error('获取翻译内容失败:', error);
              setTranslatedText('翻译完成，但获取内容失败，请刷新重试');
              setTranslating(false);
              setTranslationTaskId(null);
            });
        } else if (status.status === 'failed') {
          console.error('翻译失败:', status.error_message || '未知错误');
          setTranslating(false);
          setTranslationTaskId(null);
        }
      },
      onError: (error) => {
        console.error('获取翻译状态失败:', error);
        setTranslating(false);
        setTranslationTaskId(null);
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
      <Box sx={{ flexGrow: 1, overflow: 'hidden', minHeight: 0 }}>
        <Grid container spacing={2} sx={{ height: '100%', margin: 0, width: '100%' }}>
          {/* 原文栏 */}
          <Grid item xs={12} md={6} sx={{ height: '100%', paddingLeft: '0 !important' }}>
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
                lineHeight: 1.6,
                '& p': {
                  marginBottom: '1em',
                  textIndent: '2em'
                },
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                  marginTop: '1.5em',
                  marginBottom: '0.5em',
                  fontWeight: 'bold'
                },
                '& em, & i': {
                  fontStyle: 'italic'
                },
                '& strong, & b': {
                  fontWeight: 'bold'
                }
              }}>
                <div 
                  dangerouslySetInnerHTML={{ 
                    __html: highlightedText ? 
                      originalText.replace(
                        new RegExp(`(${highlightedText})`, 'gi'),
                        '<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 4px;">$1</mark>'
                      ) : 
                      originalText 
                  }}
                />
              </Box>
            </Paper>
          </Grid>

          {/* 译文栏 */}
          <Grid item xs={12} md={6} sx={{ height: '100%', paddingRight: '0 !important' }}>
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
                lineHeight: 1.8,
                '& p': {
                  marginBottom: '1em',
                  textIndent: '2em'
                },
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                  marginTop: '1.5em',
                  marginBottom: '0.5em',
                  fontWeight: 'bold'
                },
                '& em, & i': {
                  fontStyle: 'italic'
                },
                '& strong, & b': {
                  fontWeight: 'bold'
                }
              }}>
                {translatedText ? (
                  <div 
                    dangerouslySetInnerHTML={{ 
                      __html: highlightedText ? 
                        translatedText.replace(
                          new RegExp(`(${highlightedText})`, 'gi'),
                          '<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 4px;">$1</mark>'
                        ) : 
                        translatedText 
                    }}
                  />
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