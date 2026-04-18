/**
 * Send a single iMessage via Photon Spectrum and exit.
 * Reads credentials and message details from environment variables:
 *   PHOTON_PROJECT_ID, PHOTON_SECRET_KEY, SEND_PHONE, SEND_MESSAGE
 */
import { Spectrum } from "spectrum-ts";
import { imessage } from "spectrum-ts/providers/imessage";

const { PHOTON_PROJECT_ID, PHOTON_SECRET_KEY, SEND_PHONE, SEND_MESSAGE } = process.env;

if (!PHOTON_PROJECT_ID || !PHOTON_SECRET_KEY) {
  console.error("Missing PHOTON_PROJECT_ID or PHOTON_SECRET_KEY");
  process.exit(1);
}

if (!SEND_PHONE || !SEND_MESSAGE) {
  console.error("Missing SEND_PHONE or SEND_MESSAGE");
  process.exit(1);
}

let app;
try {
  app = await Spectrum({
    projectId: PHOTON_PROJECT_ID,
    projectSecret: PHOTON_SECRET_KEY,
    providers: [imessage.config()],
  });

  const im = imessage(app);
  const user = await im.user(SEND_PHONE);
  const space = await im.space(user);
  await space.send(SEND_MESSAGE);

  console.log("sent");
  await app.stop();
  process.exit(0);
} catch (err) {
  console.error(err.message ?? err);
  if (app) await app.stop().catch(() => {});
  process.exit(1);
}
