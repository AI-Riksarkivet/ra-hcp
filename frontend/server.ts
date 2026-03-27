/**
 * Custom Deno server entry point that fixes the URL protocol for
 * TLS-terminating reverse proxies (nginx ingress).
 *
 * Problem: nginx terminates HTTPS and forwards HTTP to Deno. SvelteKit's
 * CSRF check compares the browser's Origin (https://) against the request
 * URL (http://) and rejects POST requests as cross-site.
 *
 * Fix: read X-Forwarded-Proto and construct a new Request with the correct
 * protocol before passing it to SvelteKit. This is what adapter-node does
 * internally via PROTOCOL_HEADER, but the Deno adapter doesn't support it.
 */
import rawDeployConfig from "./.deno-deploy/deploy.json" with { type: "json" };
import rawSvelteData from "./.deno-deploy/svelte.json" with { type: "json" };
import { prepareServer } from "./.deno-deploy/handler.ts";

const innerHandler = prepareServer(rawSvelteData, rawDeployConfig, Deno.cwd());

const handler: Deno.ServeHandler = async (req, info) => {
  const proto = req.headers.get("x-forwarded-proto");
  if (proto === "https" && new URL(req.url).protocol === "http:") {
    const url = new URL(req.url);
    url.protocol = "https:";
    req = new Request(url.toString(), {
      method: req.method,
      headers: req.headers,
      body: req.body,
      // @ts-ignore — duplex required for streaming request bodies
      duplex: "half",
    });
  }
  return innerHandler(req, info);
};

Deno.serve(handler);
