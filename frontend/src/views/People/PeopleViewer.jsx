// src/components/PeopleViewer.jsx
import React, { useEffect, useState } from 'react';
import { getPeople } from '../services/api';
import Loader from './ui/Loader';
import ErrorBox from './ui/ErrorBox';
import { useTree } from '../context/TreeContext';

const PeopleViewer = () => {
  const { treeId } = useTree();
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPeople(treeId)
      .then(data => {
        console.log("Fetched people for tree", treeId, ":", data);
        setPeople(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching people:", err);
        setError("Failed to load people.");
        setLoading(false);
      });
  }, [treeId]);

  if (loading) return <Loader />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div style={{ padding: '1rem' }}>
      <h2>People in Tree</h2>
      {people.length === 0 ? (
        <p>No people found.</p>
      ) : (
        <ul>
          {people.map(person => (
            <li key={person.id}>
              {person.name || 'Unnamed'} – {person.occupation || 'No occupation'}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default PeopleViewer;
