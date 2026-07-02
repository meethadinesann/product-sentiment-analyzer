// This component shows one review as a card with color based on sentiment
function ReviewCard({ review }) {
  // Color coding: green=positive, red=negative, gray=neutral
  const sentimentColors = {
    positive: 'green',
    negative: 'red',
    neutral: 'gray'
  };

  const color = sentimentColors[review.sentiment] || 'gray';

  return (
    <div style={{
      border: '1px solid #ccc',
      padding: '15px',
      margin: '10px',
      borderLeft: 5px solid ${color},
      borderRadius: '5px'
    }}>
      <p><b>{review.reviewer_name}</b> — {review.review_date} — ⭐ {review.rating}/5</p>
      <p>{review.review_text}</p>
      <p style={{ color: color }}><b>{review.sentiment?.toUpperCase()}</b></p>
    </div>
  );
}

export default ReviewCard;