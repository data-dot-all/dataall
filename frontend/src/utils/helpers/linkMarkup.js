export const createLinkMarkup = (text, color) => {
  // Define the components of the regex pattern

  // Matches optional protocol (http:// or https://)
  const protocol = '(https?://)?';

  // Matches any domain or subdomain
  const domain = '([a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,}';

  // Matches paths and query strings, excluding certain special characters
  const pathAndQuery = '(\\/[^\\s()$@]*)?(\\?[\\w=&-]*)?(#[\\w\\-]*)?';

  // Combine all parts into the final regex pattern
  const urlRegex = new RegExp(
    `(${protocol})?(${domain})(?=\\s|\\/|$)${pathAndQuery}(?=\\s|$)`,
    'gi'
  );

  return text.replace(urlRegex, (fullMatch) => {
    const decodedUrl = decodeURIComponent(fullMatch);

    // Determine the correct href value for the anchor tag
    let href = '';
    if (decodedUrl.startsWith('https://') || decodedUrl.startsWith('http://')) {
      href = decodedUrl;
    } else {
      href = `https://${decodedUrl}`;
    }

    // Return the HTML string for the anchor tag with the correct href and style
    return `<a href="${href}" style="color: ${color};" target="_blank" rel="noopener noreferrer">${fullMatch}</a>`;
  });
};
