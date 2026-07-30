export function decodeToken(token) {
  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(atob(payload));
    return decoded; // { sub, user_id, is_admin, exp }
  } catch {
    return null;
  }
}