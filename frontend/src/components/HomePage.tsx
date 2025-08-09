import React, { useState } from 'react';
import {
  Box,
  Container,
  Tabs,
  Tab,
  Typography,
  Paper,
  Fade
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  LibraryBooks as LibraryIcon
} from '@mui/icons-material';
import BookUpload from './BookUpload';
import BookLibrary from './BookLibrary';
import type { BookInfo } from '../types/book';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`main-tabpanel-${index}`}
      aria-labelledby={`main-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Fade in={true} timeout={300}>
          <Box sx={{ py: 3 }}>
            {children}
          </Box>
        </Fade>
      )}
    </div>
  );
};

const HomePage: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleBookSelect = (book: BookInfo) => {
    // 当从书库选择书籍时，会通过BookLibrary组件内部的useBookStore自动设置
    // 这里不需要额外处理，App组件会检测到currentBook的变化并切换到BookReader
  };

  const handleUploadSuccess = (book: BookInfo) => {
    // 上传成功后也会自动设置currentBook并切换到BookReader
    // 这里可以选择性地切换到书库标签页以显示新上传的书籍
    setCurrentTab(0); // 切换到书库标签页（现在是index 0）
  };

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom
          sx={{ 
            fontWeight: 'bold',
            background: 'linear-gradient(45deg, #1976d2, #42a5f5)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1
          }}
        >
          AI 有声书工坊
        </Typography>
        <Typography 
          variant="h6" 
          color="text.secondary" 
          sx={{ mb: 3 }}
        >
          上传电子书，AI智能翻译，语音合成，打造专属有声读物
        </Typography>
      </Box>

      <Paper 
        elevation={3} 
        sx={{ 
          borderRadius: 3,
          overflow: 'hidden',
          backgroundColor: 'background.paper'
        }}
      >
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange}
            centered
            variant="fullWidth"
            sx={{
              '& .MuiTab-root': {
                minHeight: 64,
                fontSize: '1rem',
                fontWeight: 600,
                textTransform: 'none'
              }
            }}
          >
            <Tab 
              icon={<LibraryIcon sx={{ mb: 0.5 }} />}
              label="我的书库" 
              id="main-tab-0"
              aria-controls="main-tabpanel-0"
            />
            <Tab 
              icon={<UploadIcon sx={{ mb: 0.5 }} />}
              label="上传新书" 
              id="main-tab-1"
              aria-controls="main-tabpanel-1"
            />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <Box sx={{ px: 3 }}>
            <BookLibrary onBookSelect={handleBookSelect} />
          </Box>
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <Box sx={{ px: 3 }}>
            <BookUpload onUploadSuccess={handleUploadSuccess} />
          </Box>
        </TabPanel>
      </Paper>

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          支持 EPUB 格式电子书 • AI 翻译 • 语音合成 • 在线阅读
        </Typography>
      </Box>
    </Container>
  );
};

export default HomePage;
