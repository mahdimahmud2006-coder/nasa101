// Fetch the default comparison early. Shared case links keep their own image requests.
const atlasPreviewRequest = document.currentScript;
const atlasPreviewLocation = new URL(location.href);
const atlasDefaultQuery = [...atlasPreviewLocation.searchParams.keys()].every(key => key === 'benchmark');
if (atlasDefaultQuery && (!location.hash || location.hash === '#atlas')) {
  for(const source of [atlasPreviewRequest.dataset.preview,atlasPreviewRequest.dataset.reference]){
    const preview = document.createElement('link');
    preview.rel = 'preload';
    preview.as = 'image';
    preview.fetchPriority = 'high';
    preview.href = source;
    document.head.append(preview);
  }
}
