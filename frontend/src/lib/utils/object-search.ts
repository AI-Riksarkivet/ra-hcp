/**
 * Compute the server-side object-listing query for the bucket browser.
 *
 * With no search term we list the navigated prefix using the current view
 * (folder vs flat). With a search term we keep the navigated prefix + term as
 * the S3 prefix filter, but PRESERVE the current view mode:
 *   - folder view (delimiter) → matching sub-folders (CommonPrefixes) AND files
 *     at this level are returned, so folders remain searchable and viewable.
 *   - flat view → recursive match across the whole bucket (no folder grouping).
 *
 * Previously this forced `flat: true` on any search, which made the backend
 * drop CommonPrefixes — so folders silently disappeared from search results.
 * Use the flat toggle for a recursive cross-folder object search.
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
  return { prefix: navigatedPrefix + term, flat };
}
