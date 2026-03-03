const base64URLEncode = (buffer) =>
    btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');

const sha256 = async (plain) => {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  return await crypto.subtle.digest('SHA-256', data);
};

export const generatePKCE = async () => {
  // 96 bytes = 128 characters after base64url encoding (max per RFC 7636)
  const verifier = base64URLEncode(crypto.getRandomValues(new Uint8Array(96)));
  const challenge = base64URLEncode(await sha256(verifier));
  return { verifier, challenge };
};

export const generateState = () =>
  base64URLEncode(crypto.getRandomValues(new Uint8Array(32)));