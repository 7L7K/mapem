import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Drawer = ({ children, onClose }) => (
  <motion.div
    initial={{ x: '100%' }}
    animate={{ x: 0 }}
    exit={{ x: '100%' }}
    transition={{ type: 'tween' }}
    className="fixed right-0 top-0 h-full w-80 bg-neutral-900 text-neutral-100 shadow-lg z-50 overflow-y-auto"
  >
    <div className="p-4 border-b border-neutral-800 flex justify-between items-center">
      <h4 className="font-semibold">Person Details</h4>
      <button
        onClick={onClose}
        className="text-neutral-400 hover:text-neutral-200 transition"
      >
        ✕
      </button>
    </div>
    {children}
  </motion.div>
);

const PersonDrawer = ({ personId, personName, movements, onClose, onReresolve }) => (
  <AnimatePresence>
    {personId && (
      <Drawer onClose={onClose}>
        <div className="p-4 space-y-4">
          <div>
            <p className="text-sm text-neutral-400">ID: {personId}</p>
            <h2 className="text-lg font-bold">{personName}</h2>
          </div>

          <div>
            <h3 className="font-medium mb-2">Movements</h3>
            <ul className="space-y-1">
              {movements.map((m, i) => (
                <li key={i} className="text-sm">
                  <span className="capitalize">{m.event_type}</span>{' '}
                  {m.year && `(${m.year})`} — {m.location}
                </li>
              ))}
            </ul>
          </div>

          <div className="pt-3 border-t border-neutral-800">
            <button
              onClick={onReresolve}
              className="px-3 py-2 bg-yellow-400 text-black rounded font-semibold hover:bg-yellow-300"
            >
              Re-resolve place
            </button>
          </div>
        </div>
      </Drawer>
    )}
  </AnimatePresence>
);

export default PersonDrawer;
