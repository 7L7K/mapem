import React, { useState } from 'react';
import { createShareLink } from '@lib/api/api';
import { useTree } from '@shared/context/TreeContext';
import { useSearch } from '@shared/context/SearchContext';

export default function ShareLinkButton() {
    const { treeId } = useTree();
    const { filters } = useSearch();
    const [url, setUrl] = useState('');
    const [busy, setBusy] = useState(false);

    const onShare = async () => {
        if (!treeId) return;
        setBusy(true);
        try {
            const { token } = await createShareLink(treeId, filters);
            const shareUrl = `${window.location.origin}/map/${treeId}?token=${encodeURIComponent(token)}`;
            setUrl(shareUrl);
            await navigator.clipboard.writeText(shareUrl);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="absolute right-4 bottom-16 z-50">
            <button onClick={onShare} disabled={busy} className="bg-black/70 text-white text-xs px-3 py-2 rounded-md border border-white/10 hover:bg-black/80">
                {busy ? 'Generating…' : 'Share view'}
            </button>
            {url && (
                <div className="mt-2 text-[10px] text-white/70 max-w-[240px] break-words">Copied: {url}</div>
            )}
        </div>
    );
}


