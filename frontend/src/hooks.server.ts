import type { Handle } from "@sveltejs/kit";
import { enumerateSessions } from "$lib/server/sessions.js";

export const handle: Handle = ({ event, resolve }) => {
  const token = event.cookies.get("hcp_token");
  if (token) {
    event.locals.token = token;
  }
  event.locals.sessions = enumerateSessions(event.cookies, token);
  return resolve(event);
};
