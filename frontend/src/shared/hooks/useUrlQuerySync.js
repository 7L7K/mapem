import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// Handy parser/serializer for selected filter subset into URL query params
// Mapped params:
// person -> q
// selectedPersonId -> pid
// selectedFamilyId -> fid
// compareIds[] -> compare (CSV)
// yearRange[min,max] -> yr=min-max
// mode -> mode

export default function useUrlQuerySync(filters, setFilters, mode, setMode) {
    const location = useLocation();
    const navigate = useNavigate();

    const parseQuery = (search) => {
        const params = new URLSearchParams(search);
        const q = params.get('q') || '';
        const pid = params.get('pid');
        const fid = params.get('fid');
        const compare = params.get('compare');
        const yr = params.get('yr');
        const modeParam = params.get('mode');

        const parsed = {};
        if (q) parsed.person = q;
        if (pid) parsed.selectedPersonId = pid;
        if (fid) parsed.selectedFamilyId = fid;
        if (compare) parsed.compareIds = compare.split(',').filter(Boolean);
        if (yr && yr.includes('-')) {
            const [min, max] = yr.split('-').map((v) => parseInt(v, 10));
            if (!Number.isNaN(min) && !Number.isNaN(max)) parsed.yearRange = [min, max];
        }
        return { parsed, modeParam };
    };

    const serializeQuery = (f, m) => {
        const params = new URLSearchParams();
        if (f.person) params.set('q', f.person);
        if (f.selectedPersonId) params.set('pid', f.selectedPersonId);
        if (f.selectedFamilyId) params.set('fid', f.selectedFamilyId);
        if (Array.isArray(f.compareIds) && f.compareIds.length)
            params.set('compare', f.compareIds.join(','));
        if (Array.isArray(f.yearRange) && f.yearRange.length === 2)
            params.set('yr', `${f.yearRange[0]}-${f.yearRange[1]}`);
        if (m && m !== 'default') params.set('mode', m);
        return params.toString();
    };

    // On mount: hydrate filters from URL
    useEffect(() => {
        const { parsed, modeParam } = parseQuery(location.search);
        const hasAny = Object.keys(parsed).length > 0 || !!modeParam;
        if (hasAny) {
            setFilters(parsed);
            if (modeParam) setMode(modeParam);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // When filters or mode change, update URL (replace, not push)
    const queryString = useMemo(() => serializeQuery(filters, mode), [filters, mode]);
    useEffect(() => {
        const current = location.search.startsWith('?') ? location.search.slice(1) : location.search;
        if (current !== queryString) {
            navigate({ search: queryString ? `?${queryString}` : '' }, { replace: true });
        }
    }, [queryString, location.search, navigate]);
}


