// src/components/Timeline.jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import { useTree } from '../context/TreeContext';

const Timeline = () => {
  const { treeId } = useTree();
  const [timelineData, setTimelineData] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    axios.get(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050'}/api/timeline/${treeId}`)
      .then(res => {
        console.log("Timeline data for tree", treeId, ":", res.data);
        setTimelineData(res.data);
      })
      .catch(err => {
        setError("Failed to load timeline");
        console.error("❌ Timeline fetch error:", err);
      });
  }, [treeId]);

  if (error) return <ErrorBox message={error} />;
  if (!timelineData.length) return <Loader />;

  return (
    <div>
      <h2>Timeline</h2>
      <ul>
        {timelineData.map((item, i) => (
          <li key={i}>
            <strong>{item.year}</strong> - {item.event}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Timeline;
