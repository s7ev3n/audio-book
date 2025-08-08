import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Divider,
  Fab,
  Drawer,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';

import { useBookStore } from '../store/bookStore';
import { epubAPI } from '../services/api';
import ChapterList from './ChapterList';
import TextDisplay from './TextDisplay';
import AudioPlayer from './AudioPlayer';
import TranslationProgress from './TranslationProgress';

const BookReader: React.FC = () => {
  const { bookId } = useParams<{ bookId: string }>();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const {
    currentBook,
    chapters,
    currentChapter,
    currentChapterIndex,
    setChapters,
    setCurrentChapter
  } = useBookStore();

  // 获取章节列表
  const { data: chaptersData, isLoading } = useQuery(
    ['chapters', bookId],
    () => bookId ? epubAPI.getChapters(bookId) : Promise.resolve([]),
    {
      enabled: !!bookId,
      onSuccess: (data) => {
        setChapters(data);
        if (data.length > 0 && !currentChapter) {
          setCurrentChapter(data[0], 0);
        }
      }
    }
  );

  const handleChapterSelect = (chapter: any, index: number) => {
    setCurrentChapter(chapter, index);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <Typography>加载中...</Typography>
      </Box>
    );
  }

  if (!currentBook || !bookId) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="h6">未找到书籍信息</Typography>
      </Box>
    );
  }

  const drawerContent = (
    <Box sx={{ width: 300, height: '100%' }}>
      <ChapterList
        chapters={chapters}
        currentChapter={currentChapter}
        onChapterSelect={handleChapterSelect}
        isPlaying={isPlaying}
      />
    </Box>
  );

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      {/* 移动端菜单按钮 */}
      {isMobile && (
        <Fab
          color="primary"
          onClick={toggleDrawer}
          sx={{
            position: 'fixed',
            bottom: 80,
            left: 16,
            zIndex: 1000
          }}
        >
          <MenuIcon />
        </Fab>
      )}

      {/* 移动端侧边栏 */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        sx={{ display: { xs: 'block', md: 'none' } }}
      >
        {drawerContent}
      </Drawer>

      <Box sx={{ flexGrow: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 桌面端侧边栏 */}
        {!isMobile && (
          <Paper 
            elevation={1} 
            sx={{ 
              width: 300, 
              height: '100%',
              overflow: 'hidden',
              borderRadius: 0 
            }}
          >
            {drawerContent}
          </Paper>
        )}

        {/* 主内容区域 */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
          {/* 翻译进度显示 */}
          <TranslationProgress />
          
          {/* 双栏文本显示 */}
          <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
            {currentChapter ? (
              <TextDisplay
                bookId={bookId}
                chapter={currentChapter}
              />
            ) : (
              <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100%' 
              }}>
                <Typography variant="h6" color="text.secondary">
                  请选择一个章节开始阅读
                </Typography>
              </Box>
            )}
          </Box>

          {/* 音频播放器 */}
          <Paper elevation={3} sx={{ mt: 'auto' }}>
            <AudioPlayer
              bookId={bookId}
              chapter={currentChapter}
              chapters={chapters}
              currentIndex={currentChapterIndex}
              onChapterChange={handleChapterSelect}
            />
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default BookReader;