import DOMPurify from 'dompurify';

export const SanitizedHTML = ({ dirtyHTML }) => {
  const defaultOptions = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'style']
  };

  const sanitizedHtml = DOMPurify.sanitize(dirtyHTML, defaultOptions);

  return <div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />;
};
