import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton
} from '@mui/material';
import { Home, Upload, Book } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useBookStore } from '../store/bookStore';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { currentBook, clearBook } = useBookStore();

  const handleHomeClick = () => {
    navigate('/');
  };

  const handleUploadClick = () => {
    clearBook();
    navigate('/upload');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Book sx={{ mr: 2 }} />
          <Typography variant="h6" component="div">
            📚 Audio Book Translator
          </Typography>
        </Box>
        
        {currentBook && (
          <Typography variant="subtitle1" sx={{ mr: 2 }}>
            《{currentBook.title}》 - {currentBook.author}
          </Typography>
        )}
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton color="inherit" onClick={handleHomeClick}>
            <Home />
          </IconButton>
          <Button 
            color="inherit" 
            startIcon={<Upload />}
            onClick={handleUploadClick}
          >
            上传新书
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;