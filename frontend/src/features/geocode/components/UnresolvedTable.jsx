// frontend/src/features/geocode/components/UnresolvedTable.jsx
import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import PropTypes from "prop-types";
import  Spinner  from "@shared/components/ui/spinner";
import { Badge } from "@shared/components/ui/badge";
import  Button from "@shared/components/ui/button";
import { formatDateWithTime } from "@shared/utils/formatters";
import debounce from "lodash.debounce";
import FixModal from "./FixModal";
import { FixedSizeList as List } from "react-window";
import AutoSizer from "react-virtualized-auto-sizer";
import { saveAs } from "file-saver";
import { ResizableBox } from "react-resizable";
import "react-resizable/css/styles.css";
import axios from "axios";
import { devLog } from "@shared/utils/devLogger";

const HEADERS = [
  { key: "id", label: "ID", width: 60 },
  { key: "rawName", label: "Raw Name", width: 200 },
  { key: "normalizedName", label: "Normalized", width: 200 },
  { key: "confidence", label: "Confidence", width: 100 },
  { key: "eventCount", label: "# Events", width: 80 },
  { key: "lastSeen", label: "Last Seen", width: 150 },
  { key: "action", label: "Action", width: 100 },
];

export default function UnresolvedTable({ data, loading, refresh }) {
  const [search, setSearch] = useState("");
  const [filtered, setFiltered] = useState(data);
  const [sortKey, setSortKey] = useState("lastSeen");
  const [sortAsc, setSortAsc] = useState(false);
  const [modalItem, setModalItem] = useState(null);
  const [colWidths, setColWidths] = useState(HEADERS.map(h => h.width));
  const containerRef = useRef();

  // filter
  const doFilter = useMemo(
    () =>
      debounce(term => {
        const t = term.toLowerCase();
        setFiltered(
          data.filter(item =>
            item.rawName.toLowerCase().includes(t) ||
            (item.normalizedName || "").toLowerCase().includes(t)
          )
        );
      }, 300),
    [data]
  );
  useEffect(() => {
    doFilter(search);
  }, [search, data, doFilter]);

  // sort
  const sorted = useMemo(() => {
    const arr = [...filtered].sort((a, b) => {
      let va = a[sortKey],
        vb = b[sortKey];
      if (sortKey === "lastSeen") {
        va = new Date(va);
        vb = new Date(vb);
      }
      return va < vb ? (sortAsc ? -1 : 1) : va > vb ? (sortAsc ? 1 : -1) : 0;
    });
    return arr;
  }, [filtered, sortKey, sortAsc]);

  // CSV export
  const exportCSV = () => {
    const headerRow = HEADERS.map(h => `"${h.label}"`).join(",");
    const rows = sorted.map(item =>
      [
        item.id,
        item.rawName,
        item.normalizedName || "",
        `${Math.round(item.confidence * 100)}%`,
        item.eventCount,
        formatDateWithTime(item.lastSeen),
      ]
        .map(v => `"${v}"`)
        .join(",")
    );
    const csv = [headerRow, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, "unresolved_locations.csv");
  };

  // header resize
  const onHeaderResize = (i, w) => {
    setColWidths(cw => {
      const copy = [...cw];
      copy[i] = w;
      return copy;
    });
  };

  // row renderer
  const Row = useCallback(
    ({ index, style }) => {
      const item = sorted[index];
      return (
        <div
          style={style}
          className="flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 px-2"
          tabIndex={0}
          onKeyDown={e => e.key === "Enter" && setModalItem(item)}
          onClick={() => devLog("UnresolvedTable", "👀 row click", item)}
        >
          {HEADERS.map((hdr, i) => (
            <div
              key={hdr.key}
              style={{ width: colWidths[i] }}
              className="px-1"
              role={hdr.key === "action" ? "button" : "cell"}
            >
              {hdr.key === "confidence" ? (
                <Badge
                  variant={
                    item.confidence >= 0.8
                      ? "success"
                      : item.confidence >= 0.5
                      ? "warning"
                      : "destructive"
                  }
                >
                  {Math.round(item.confidence * 100)}%
                </Badge>
              ) : hdr.key === "action" ? (
                <Button
                  size="sm"
                  onClick={e => {
                    e.stopPropagation();
                    devLog("UnresolvedTable", "🛠️ Fix clicked", item);
                    setModalItem(item);
                  }}
                >
                  Fix
                </Button>
              ) : hdr.key === "lastSeen" ? (
                formatDateWithTime(item.lastSeen)
              ) : hdr.key === "id" ? (
                <button
                  onClick={e => {
                    e.stopPropagation();
                    document
                      .getElementById(`map-pin-${item.id}`)
                      ?.scrollIntoView();
                  }}
                >
                  {item.id}
                </button>
              ) : (
                item[hdr.key] || "—"
              )}
            </div>
          ))}
        </div>
      );
    },
    [sorted, colWidths]
  );

  if (loading) return <Spinner />;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <input
          type="text"
          className="border px-2 py-1 rounded w-1/3"
          placeholder="Search..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          aria-label="Filter unresolved locations"
        />
        <div className="space-x-2">
          <Button onClick={refresh}>Refresh</Button>
          <Button onClick={exportCSV}>Export CSV</Button>
        </div>
      </div>

      <div className="flex bg-gray-200 dark:bg-gray-700 px-2">
        {HEADERS.map((hdr, i) => (
          <ResizableBox
            key={hdr.key}
            width={colWidths[i]}
            height={30}
            axis="x"
            resizeHandles={["e"]}
            handle={<span className="cursor-col-resize px-1">⋮</span>}
            onResizeStop={(e, { size }) => onHeaderResize(i, size.width)}
          >
            <div
              className="font-semibold cursor-pointer"
              onClick={() => {
                if (sortKey === hdr.key) setSortAsc(!sortAsc);
                else {
                  setSortKey(hdr.key);
                  setSortAsc(true);
                }
              }}
              aria-sort={
                sortKey === hdr.key
                  ? sortAsc
                    ? "ascending"
                    : "descending"
                  : "none"
              }
            >
              {hdr.label}
            </div>
          </ResizableBox>
        ))}
      </div>

      <div ref={containerRef} style={{ height: 400 }}>
        <AutoSizer>
          {({ height, width }) => (
            <List height={height} itemCount={sorted.length} itemSize={35} width={width}>
              {Row}
            </List>
          )}
        </AutoSizer>
      </div>

      {modalItem && (
        <FixModal
          isOpen={!!modalItem}
          locationId={modalItem.id}
          onClose={() => setModalItem(null)}
          onSuccess={refresh}
        />
      )}
    </div>
  );
}

UnresolvedTable.propTypes = {
  data: PropTypes.array.isRequired,
  loading: PropTypes.bool,
  refresh: PropTypes.func.isRequired,
};

UnresolvedTable.defaultProps = {
  loading: false,
};
