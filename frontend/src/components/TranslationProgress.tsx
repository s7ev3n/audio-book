import React from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Collapse,
  Alert,
  Chip
} from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  Schedule,
  Error
} from '@mui/icons-material';

import { useBookStore } from '../store/bookStore';

const TranslationProgress: React.FC = () => {
  const { 
    isTranslating, 
    isGeneratingAudio,
    currentChapter,
    translatedText,
    audioUrl
  } = useBookStore();

  const hasTranslation = Boolean(translatedText);
  const hasAudio = Boolean(audioUrl);
  const showProgress = isTranslating || isGeneratingAudio;

  if (!showProgress && !hasTranslation && !hasAudio) {
    return null;
  }

  const getTranslationStatus = () => {
    if (isTranslating) return { icon: <Schedule />, text: '翻译中...', color: 'warning' as const };
    if (hasTranslation) return { icon: <CheckCircle />, text: '翻译完成', color: 'success' as const };
    return { icon: <RadioButtonUnchecked />, text: '未开始翻译', color: 'default' as const };
  };

  const getAudioStatus = () => {
    if (isGeneratingAudio) return { icon: <Schedule />, text: '语音生成中...', color: 'warning' as const };
    if (hasAudio) return { icon: <CheckCircle />, text: '语音已生成', color: 'success' as const };
    if (hasTranslation) return { icon: <RadioButtonUnchecked />, text: '可生成语音', color: 'info' as const };
    return { icon: <RadioButtonUnchecked />, text: '需先翻译', color: 'default' as const };
  };

  const translationStatus = getTranslationStatus();
  const audioStatus = getAudioStatus();

  return (
    <Collapse in={showProgress || hasTranslation || hasAudio}>
      <Paper 
        elevation={1} 
        sx={{ 
          p: 2, 
          mb: 2, 
          bgcolor: 'background.default',
          borderLeft: 3,
          borderColor: isTranslating || isGeneratingAudio ? 'warning.main' : 'success.main'
        }}
      >
        {/* 当前章节信息 */}
        {currentChapter && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              当前章节: {currentChapter.title}
            </Typography>
          </Box>
        )}

        {/* 进度条 */}
        {(isTranslating || isGeneratingAudio) && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress 
              variant="indeterminate" 
              sx={{ 
                height: 6, 
                borderRadius: 3,
                bgcolor: 'action.hover'
              }} 
            />
          </Box>
        )}

        {/* 状态指示器 */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* 翻译状态 */}
          <Chip
            icon={translationStatus.icon}
            label={translationStatus.text}
            color={translationStatus.color}
            variant={isTranslating ? 'filled' : 'outlined'}
            size="small"
          />

          {/* 语音状态 */}
          <Chip
            icon={audioStatus.icon}
            label={audioStatus.text}
            color={audioStatus.color}
            variant={isGeneratingAudio ? 'filled' : 'outlined'}
            size="small"
          />
        </Box>

        {/* 完成提示 */}
        {hasTranslation && hasAudio && !isTranslating && !isGeneratingAudio && (
          <Alert 
            severity="success" 
            sx={{ mt: 2 }}
            variant="outlined"
          >
            🎉 章节翻译和语音生成已完成，可以开始阅读和收听了！
          </Alert>
        )}

        {/* 错误提示 - 这里可以扩展错误状态处理 */}
        {/* 暂时先不显示错误状态，后续可以从store中获取错误信息 */}
      </Paper>
    </Collapse>
  );
};

export default TranslationProgress;