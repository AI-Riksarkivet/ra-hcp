import type { Handle } from "@sveltejs/kit";

export const handle: Handle = ({ event, resolve }) => {
  const token = event.cookies.get("hcp_token");
  if (token) {
    event.locals.token = token;
  }
  return resolve(event);
};
