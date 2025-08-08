import React from 'react';
import {
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Box,
  Chip,
  Divider,
  Paper
} from '@mui/material';
import { PlayArrow, Pause } from '@mui/icons-material';
import { ChapterInfo } from '../types/book';

interface ChapterListProps {
  chapters: ChapterInfo[];
  currentChapter: ChapterInfo | null;
  onChapterSelect: (chapter: ChapterInfo, index: number) => void;
  isPlaying?: boolean;
}

const ChapterList: React.FC<ChapterListProps> = ({
  chapters,
  currentChapter,
  onChapterSelect,
  isPlaying = false
}) => {
  const formatContentLength = (length: number) => {
    if (length > 1000) {
      return `${Math.round(length / 1000)}k 字符`;
    }
    return `${length} 字符`;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 标题 */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" gutterBottom>
          📚 章节目录
        </Typography>
        <Typography variant="body2" color="text.secondary">
          共 {chapters.length} 个章节
        </Typography>
      </Box>

      {/* 章节列表 */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ p: 0 }}>
          {chapters.map((chapter, index) => {
            const isSelected = currentChapter?.id === chapter.id;
            
            return (
              <React.Fragment key={chapter.id}>
                <ListItem disablePadding>
                  <ListItemButton
                    selected={isSelected}
                    onClick={() => onChapterSelect(chapter, index)}
                    sx={{
                      py: 1.5,
                      px: 2,
                      '&.Mui-selected': {
                        bgcolor: 'primary.light',
                        color: 'primary.contrastText',
                        '&:hover': {
                          bgcolor: 'primary.main',
                        }
                      }
                    }}
                  >
                    <Box sx={{ width: '100%' }}>
                      {/* 章节号和播放状态 */}
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Chip 
                          label={`第 ${index + 1} 章`} 
                          size="small" 
                          variant={isSelected ? "filled" : "outlined"}
                          color={isSelected ? "secondary" : "default"}
                          sx={{ mr: 1, fontSize: '0.7rem' }}
                        />
                        
                        {/* 播放状态图标 */}
                        {isSelected && (
                          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                            {isPlaying ? (
                              <Pause fontSize="small" sx={{ opacity: 0.8 }} />
                            ) : (
                              <PlayArrow fontSize="small" sx={{ opacity: 0.8 }} />
                            )}
                          </Box>
                        )}
                      </Box>
                      
                      {/* 章节标题 */}
                      <Typography
                        variant="subtitle2"
                        sx={{
                          fontWeight: isSelected ? 600 : 400,
                          lineHeight: 1.3,
                          mb: 0.5,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}
                      >
                        {chapter.title}
                      </Typography>
                      
                      {/* 章节信息 */}
                      <Typography
                        variant="caption"
                        color={isSelected ? 'inherit' : 'text.secondary'}
                        sx={{ opacity: isSelected ? 0.8 : 0.7 }}
                      >
                        {formatContentLength(chapter.content_length)}
                      </Typography>
                    </Box>
                  </ListItemButton>
                </ListItem>
                
                {index < chapters.length - 1 && (
                  <Divider variant="inset" component="li" />
                )}
              </React.Fragment>
            );
          })}
        </List>
      </Box>

      {/* 底部信息 */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
        <Typography variant="caption" color="text.secondary">
          💡 点击章节开始阅读和翻译
        </Typography>
      </Box>
    </Box>
  );
};

export default ChapterList;