import React, { useCallback, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  CircularProgress,
  Alert,
  LinearProgress
} from '@mui/material';
import { Upload, CloudUpload } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation } from 'react-query';
import { useNavigate } from 'react-router-dom';

import { epubAPI } from '../services/api';
import { useBookStore } from '../store/bookStore';
import type { BookInfo } from '../types/book';

interface BookUploadProps {
  onUploadSuccess?: (book: BookInfo) => void;
}

const BookUpload: React.FC<BookUploadProps> = ({ onUploadSuccess }) => {
  const navigate = useNavigate();
  const { setCurrentBook, setChapters } = useBookStore();
  const [uploadProgress] = useState(0);

  const uploadMutation = useMutation(epubAPI.uploadEpub, {
    onSuccess: (bookInfo) => {
      setCurrentBook(bookInfo);
      setChapters(bookInfo.chapters);
      
      // 如果有回调函数，调用它
      if (onUploadSuccess) {
        onUploadSuccess(bookInfo);
      } else {
        // 如果没有回调函数，保持原有行为（直接导航）
        navigate(`/reader/${bookInfo.id}`);
      }
    },
    onError: (error: any) => {
      console.error('Upload failed:', error);
    }
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/epub+zip': ['.epub']
    },
    maxFiles: 1,
    multiple: false
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          📖 上传 EPUB 电子书
        </Typography>
        
        <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
          支持将英文EPUB电子书翻译成中文有声书
        </Typography>

        {uploadMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            上传失败：{uploadMutation.error instanceof Error ? 
              uploadMutation.error.message : '未知错误'}
          </Alert>
        )}

        {uploadMutation.isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              正在处理EPUB文件...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              请稍候，正在解析章节内容
            </Typography>
            {uploadProgress > 0 && (
              <Box sx={{ width: '100%', mt: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
              </Box>
            )}
          </Box>
        ) : (
          <>
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                bgcolor: isDragActive ? 'action.hover' : 'transparent',
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  bgcolor: 'action.hover',
                  borderColor: 'primary.main'
                }
              }}
            >
              <input {...getInputProps()} />
              <CloudUpload sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive 
                  ? '放下文件以开始上传' 
                  : '拖拽EPUB文件到这里，或点击选择文件'
                }
              </Typography>
              <Typography variant="body2" color="text.secondary">
                仅支持 .epub 格式的电子书文件
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Button
                variant="contained"
                component="label"
                startIcon={<Upload />}
                size="large"
              >
                选择EPUB文件
                <input
                  type="file"
                  accept=".epub"
                  hidden
                  onChange={handleFileSelect}
                />
              </Button>
            </Box>
          </>
        )}

        <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="h6" gutterBottom>
            📋 功能说明
          </Typography>
          <Typography variant="body2" component="div">
            <ul style={{ margin: 0, paddingLeft: '1.5em' }}>
              <li>上传英文EPUB电子书文件</li>
              <li>自动解析章节结构和内容</li>
              <li>使用AI大模型翻译成中文</li>
              <li>生成中文语音朗读</li>
              <li>双栏显示原文和译文</li>
              <li>支持音频播放和文字同步</li>
            </ul>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default BookUpload;