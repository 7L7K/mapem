// src/components/EventPanel.jsx
import React, { useEffect, useState } from 'react';
import { getEvents } from '../services/api';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import { useTree } from '../context/TreeContext';

const EventPanel = () => {
  const { treeId } = useTree();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getEvents(treeId)
      .then(data => {
        console.log("Fetched events for tree", treeId, ":", data);
        setEvents(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching events:", err);
        setError("Failed to load events.");
        setLoading(false);
      });
  }, [treeId]);

  if (loading) return <Loader />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div>
      <h2>Events</h2>
      {events.length === 0 ? (
        <div>No events found.</div>
      ) : (
        <table border="1" cellPadding="8">
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Date</th>
              <th>Date Precision</th>
              <th>Category</th>
              <th>Source Tag</th>
              <th>Individual</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {events.map(evt => (
              <tr key={evt.id}>
                <td>{evt.id}</td>
                <td>{evt.event_type}</td>
                <td>{evt.date || 'N/A'}</td>
                <td>{evt.date_precision}</td>
                <td>{evt.category}</td>
                <td>{evt.source_tag}</td>
                <td>{evt.individual ? evt.individual.name : 'N/A'}</td>
                <td>
                  {evt.location
                    ? `${evt.location.normalized_name} (${evt.location.latitude}, ${evt.location.longitude}) - Conf: ${evt.location.confidence}`
                    : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default EventPanel;
