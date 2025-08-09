import { useEffect, useRef } from 'react';

/**
 * Performance monitoring hook for development
 * Tracks render times and provides performance insights
 */
export default function usePerformance(componentName, deps = []) {
    const renderStart = useRef(performance.now());
    const renderCount = useRef(0);
    const isDev = import.meta.env.DEV;

    useEffect(() => {
        if (!isDev) return;

        renderCount.current += 1;
        const renderTime = performance.now() - renderStart.current;

        // Log slow renders (>16ms for 60fps target)
        if (renderTime > 16) {
            console.warn(`🐌 [Performance] ${componentName} render took ${renderTime.toFixed(2)}ms`);
        }

        // Log excessive re-renders
        if (renderCount.current > 10) {
            console.warn(`🔄 [Performance] ${componentName} has re-rendered ${renderCount.current} times`);
        }

        renderStart.current = performance.now();
    }, deps);

    useEffect(() => {
        if (!isDev) return;

        return () => {
            console.log(`📊 [Performance] ${componentName} unmounted after ${renderCount.current} renders`);
        };
    }, []);

    // Return performance utilities
    return {
        renderCount: renderCount.current,
        markRender: () => {
            renderStart.current = performance.now();
        }
    };
}
