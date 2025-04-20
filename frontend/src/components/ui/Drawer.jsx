// frontend/src/components/ui/Drawer.jsx
import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

export default function Drawer({
  open,
  onClose,
  children,
  className = "",
  width = "w-80",
  side = "right", // 'left' or 'right'
}) {
  const variants = {
    hidden: { x: side === "right" ? "100%" : "-100%" },
    visible: { x: 0 },
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-40 flex">
          {/* backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* panel */}
          <motion.div
            className={clsx(
              "relative bg-surface text-text shadow-xl overflow-y-auto",
              width
            )}
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={variants}
            transition={{ type: "tween", duration: 0.3 }}
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
