import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Book as BookIcon,
  MenuBook as MenuBookIcon,
  Schedule as ScheduleIcon,
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useBookStore } from '../store/bookStore';
import { getAllBooks, epubAPI } from '../services/api';
import type { BookInfo } from '../types/book';

interface BookLibraryProps {
  onBookSelect?: (book: BookInfo) => void;
}

const BookLibrary: React.FC<BookLibraryProps> = ({ onBookSelect }) => {
  const navigate = useNavigate();
  const { setCurrentBook, setChapters } = useBookStore();
  const [books, setBooks] = useState<BookInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [bookToDelete, setBookToDelete] = useState<BookInfo | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedBook, setSelectedBook] = useState<BookInfo | null>(null);

  const loadBooks = async () => {
    try {
      setLoading(true);
      setError(null);
      const booksData = await getAllBooks();
      setBooks(booksData);
    } catch (err) {
      console.error('Error loading books:', err);
      setError('加载书籍失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooks();
  }, []);

  const handleBookSelect = (book: BookInfo) => {
    if (book.id) {
      setCurrentBook(book);
      setChapters(book.chapters);
      navigate(`/reader/${book.id}`);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, book: BookInfo) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedBook(book);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedBook(null);
  };

  const handleDeleteClick = () => {
    if (selectedBook) {
      setBookToDelete(selectedBook);
      setDeleteDialogOpen(true);
      handleMenuClose();
    }
  };

  const handleDeleteConfirm = async () => {
    if (!bookToDelete) return;
    
    try {
      setDeleting(true);
      await epubAPI.deleteBook(bookToDelete.id);
      
      // 从列表中移除已删除的书籍
      setBooks(books.filter(book => book.id !== bookToDelete.id));
      
      setDeleteDialogOpen(false);
      setBookToDelete(null);
    } catch (err) {
      console.error('删除书籍失败:', err);
      setError('删除书籍失败，请重试');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setBookToDelete(null);
  };

  const formatUploadTime = (uploadTime: string) => {
    try {
      const date = new Date(uploadTime);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 1) {
        return '今天';
      } else if (diffDays === 2) {
        return '昨天';
      } else if (diffDays <= 7) {
        return `${diffDays - 1} 天前`;
      } else {
        return date.toLocaleDateString('zh-CN');
      }
    } catch {
      return uploadTime;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          正在加载书库...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Button 
          size="small" 
          onClick={loadBooks}
          sx={{ ml: 1 }}
        >
          重试
        </Button>
      </Alert>
    );
  }

  if (books.length === 0) {
    return (
      <Box 
        display="flex" 
        flexDirection="column" 
        alignItems="center" 
        justifyContent="center" 
        minHeight="300px"
        textAlign="center"
      >
        <BookIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          书库是空的
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          上传一些EPUB文件开始您的阅读之旅吧
        </Typography>
        <Button variant="outlined" onClick={loadBooks}>
          刷新
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2" gutterBottom>
          <MenuBookIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          我的书库 ({books.length} 本书)
        </Typography>
        <Button variant="outlined" size="small" onClick={loadBooks}>
          刷新
        </Button>
      </Box>

      <Grid container spacing={3}>
        {books.map((book) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={book.id}>
            <Card 
              sx={{ 
                height: '100%',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1, pb: 1, position: 'relative' }}>
                {/* 菜单按钮 */}
                <IconButton
                  sx={{ 
                    position: 'absolute', 
                    top: 8, 
                    right: 8, 
                    zIndex: 1,
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.9)'
                    }
                  }}
                  size="small"
                  onClick={(e) => handleMenuOpen(e, book)}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>

                <Tooltip title={book.title}>
                  <Typography 
                    variant="h6" 
                    component="h3" 
                    gutterBottom
                    sx={{ 
                      fontSize: '1rem',
                      fontWeight: 600,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      pr: 4 // 为菜单按钮留出空间
                    }}
                  >
                    {book.title}
                  </Typography>
                </Tooltip>

                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  gutterBottom
                  sx={{ 
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}
                >
                  作者: {book.author || '未知'}
                </Typography>

                <Box sx={{ mt: 2, mb: 1 }}>
                  <Chip 
                    label={`${book.total_chapters} 章节`}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip 
                    label={book.language.toUpperCase()}
                    size="small"
                    variant="outlined"
                    sx={{ mb: 1 }}
                  />
                </Box>

                <Box display="flex" alignItems="center" mt={1}>
                  <ScheduleIcon sx={{ fontSize: 16, color: 'text.secondary', mr: 0.5 }} />
                  <Typography variant="caption" color="text.secondary">
                    {formatUploadTime(book.upload_time)}
                  </Typography>
                </Box>
              </CardContent>

              <CardActions sx={{ pt: 0 }}>
                <Button 
                  size="small" 
                  variant="contained"
                  fullWidth
                  onClick={() => handleBookSelect(book)}
                >
                  打开阅读
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 菜单 */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
          删除书籍
        </MenuItem>
      </Menu>

      {/* 删除确认对话框 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <DialogContentText>
            您确定要删除《{bookToDelete?.title}》这本书吗？
            <br />
            <strong>此操作将删除：</strong>
            <br />
            • 书籍文件和章节内容
            <br />
            • 所有翻译文件
            <br />
            • 所有生成的音频文件
            <br />
            <br />
            <strong style={{ color: '#d32f2f' }}>此操作不可撤销！</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleting}>
            取消
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {deleting ? '删除中...' : '确认删除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BookLibrary;