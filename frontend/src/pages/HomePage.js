import { useState } from 'react';
import { triggerScrape, getReviews } from '../api/reviewApi';
import ReviewCard from '../components/ReviewCard';
import LoadingSpinner from '../components/LoadingSpinner';

// Main home page with search bar and review list
function HomePage() {
  const [url, setUrl] = useState('');
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!url) return;
    setLoading(true);
    setError('');
    try {
      await triggerScrape(url);
      const res = await getReviews();
      setReviews(res.data.reviews);
    } catch (err) {
      setError('Something went wrong. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔍 Product Sentiment Analyzer</h1>
      <div style={{ marginBottom: '20px' }}>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste Amazon/Flipkart product URL here"
          style={{ width: '70%', padding: '10px', fontSize: '16px' }}
        />
        <button
          onClick={handleSearch}
          style={{ padding: '10px 20px', marginLeft: '10px', fontSize: '16px', cursor: 'pointer' }}
        >
          Search
        </button>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {loading && <LoadingSpinner />}
      {reviews.map((review, index) => (
        <ReviewCard key={index} review={review} />
      ))}
    </div>
  );
}

export default HomePage;