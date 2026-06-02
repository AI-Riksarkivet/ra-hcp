/**
 * Compute the server-side object-listing query for the bucket browser.
 *
 * With no search term we list the navigated prefix using the current view
 * (folder vs flat). With a search term we switch to a flat (recursive) listing
 * keyed by `navigatedPrefix + term`, so the backend returns matches from across
 * the whole bucket via S3's native prefix filter — instead of the UI filtering
 * only the first page (1,000 objects) of the current folder client-side.
 */
export function objectListQuery(
  navigatedPrefix: string,
  search: string,
  flat: boolean,
): { prefix: string; flat: boolean } {
  const term = search.trim();
  if (term.length === 0) {
    return { prefix: navigatedPrefix, flat };
  }
  return { prefix: navigatedPrefix + term, flat: true };
}
