import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Code Tribunal",
    short_name: "Tribunal",
    description: "Did the code build what the ticket asked for?",
    start_url: "/",
    display: "standalone",
    background_color: "#f3e8c9",
    theme_color: "#0f9d63",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
