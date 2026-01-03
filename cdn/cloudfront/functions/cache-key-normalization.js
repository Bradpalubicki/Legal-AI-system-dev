/**
 * CloudFront Function: Cache Key Normalization
 *
 * Normalizes query strings and headers to improve cache hit rates.
 * Removes unnecessary query parameters and standardizes cache keys.
 *
 * Event Type: viewer-request
 */

function handler(event) {
    var request = event.request;
    var uri = request.uri;
    var querystring = request.querystring;

    // List of query parameters to keep for caching
    var allowedParams = [
        'version',
        'v',
        'format',
        'size',
        'quality',
        'page'
    ];

    // List of query parameters to ignore for cache key
    var ignoreParams = [
        'utm_source',
        'utm_medium',
        'utm_campaign',
        'utm_term',
        'utm_content',
        'fbclid',
        'gclid',
        '_ga',
        '_gl',
        'mc_cid',
        'mc_eid'
    ];

    // Parse query string
    var params = {};
    if (querystring) {
        var pairs = querystring.split('&');
        for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            var key = pair[0];
            var value = pair.length > 1 ? pair[1] : '';

            // Only keep allowed parameters
            if (allowedParams.indexOf(key) !== -1) {
                params[key] = value;
            }
        }
    }

    // Rebuild query string with only allowed parameters
    var newQuerystring = '';
    var sortedKeys = Object.keys(params).sort();
    for (var j = 0; j < sortedKeys.length; j++) {
        if (newQuerystring !== '') {
            newQuerystring += '&';
        }
        newQuerystring += sortedKeys[j] + '=' + params[sortedKeys[j]];
    }

    request.querystring = newQuerystring;

    // Normalize URI for static assets
    // Add default file if directory is requested
    if (uri.endsWith('/')) {
        request.uri = uri + 'index.html';
    }

    // Add .html extension for clean URLs (if file doesn't have extension)
    else if (!uri.includes('.') && !uri.startsWith('/api/')) {
        request.uri = uri + '.html';
    }

    // Lowercase the URI for case-insensitive caching
    request.uri = request.uri.toLowerCase();

    return request;
}
