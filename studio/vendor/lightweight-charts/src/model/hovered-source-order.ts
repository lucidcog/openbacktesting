export function hoveredSourceOnTopOrder<T>(sources: readonly T[], hoveredSource: unknown, enabled: boolean): readonly T[] {
	if (!enabled) {
		return sources;
	}

	const hoveredIndex = sources.indexOf(hoveredSource as T);
	if (hoveredIndex === -1 || hoveredIndex === sources.length - 1) {
		return sources;
	}

	const reorderedSources: T[] = [];
	for (let i = 0; i < sources.length; i++) {
		if (i !== hoveredIndex) {
			reorderedSources.push(sources[i]);
		}
	}
	reorderedSources.push(sources[hoveredIndex]);

	return reorderedSources;
}
