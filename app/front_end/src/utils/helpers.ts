/**
 * Retrieves a UUID from localStorage or generates a new one if not present.
 *
 * @description This function checks if a UUID is stored in the browser's localStorage under the key 'uuid'.
 * If a UUID is found, it returns the stored UUID. If no UUID is found, it uses a hardcoded UUID for development,
 * stores it in localStorage, and then returns it. This ensures that a unique identifier is consistently used
 * across different sessions for the same user.
 *
 * @returns {string} The UUID retrieved from localStorage or the hardcoded development UUID.
 *
 * @example
 * // Example usage of getUUID
 * const uuid = getUUID();
 * console.log(uuid); // Outputs the UUID from localStorage or the development UUID
 */
export function getUUID() {
  // Check if UUID is already in localStorage
  let uuid = localStorage.getItem('uuid');

  if (!uuid) {
    // Use hardcoded UUID for development
    uuid = '8d8ac610-566d-4ef0-9c22-186b2a5ed793';
    localStorage.setItem('uuid', uuid);
  }

  return uuid;
}

/**
 * Retrieves the session ID (SID) from session storage.
 *
 * @description This function fetches the 'sid' (session ID) from the browser's `sessionStorage`. If the 'sid' is not found,
 * it returns an empty string. The SID is typically used for maintaining session state in web applications.
 *
 * @returns {string} The session ID retrieved from `sessionStorage`, or an empty string if not found.
 */
export function getSID() {
  return sessionStorage.getItem('sid') || '';
}
