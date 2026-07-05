import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function TypewriterEffect({ content, speed = 15, isRunning }) {
  const [displayedContent, setDisplayedContent] = useState('');

  useEffect(() => {
    if (!content) {
      setDisplayedContent('');
      return;
    }

    // Only do typing effect if it's currently "running" or was just finished
    // If it's loaded from history, we can just show it instantly.
    // We will use a fast interval to append characters.
    const interval = setInterval(() => {
      setDisplayedContent(prev => {
        if (prev.length < content.length) {
          const remaining = content.length - prev.length;
          const chunkSize = remaining > 1000 ? 15 : remaining > 500 ? 8 : 3;
          return content.slice(0, prev.length + chunkSize);
        } else {
          clearInterval(interval);
          return prev;
        }
      });
    }, speed);

    return () => clearInterval(interval);
  }, [content, speed]);

  // If not running and already fully displayed, just render the content.
  // Actually, always render displayedContent to ensure it catches up.
  return <ReactMarkdown>{displayedContent || ''}</ReactMarkdown>;
}
