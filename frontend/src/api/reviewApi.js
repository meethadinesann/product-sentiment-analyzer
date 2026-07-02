import axios from 'axios';

// Get the backend URL from environment variable
const API_URL = process.env.REACT_APP_API_URL;

// Get all reviews from backend
export const getReviews = () => {
  return axios.get(${API_URL}/reviews);
};

// Trigger scraping for a product URL
export const triggerScrape = (url) => {
  return axios.post(${API_URL}/scrape, { url });
};

// Get sentiment summary
export const getSentiment = () => {
  return axios.get(${API_URL}/sentiment);
};