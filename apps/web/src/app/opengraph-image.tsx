import { ImageResponse } from "next/og";

/*
 * Social share card. Satori constraints: flexbox only (every multi-child div
 * needs display:flex), no color-mix(), no external fonts — the bundled default
 * face is used throughout, with letterSpacing standing in for the mono voice.
 * Fully deterministic: no data fetching, no randomness.
 */

export const alt = "Code Tribunal — Did the code build what the ticket asked for?";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const INK = "#1a1a1a";
const CREAM = "#f3e8c9";
const PAPER = "#fdf6e3";
const DANGER = "#e23c4e";
const WARNING = "#e08600";
const MUTED = "#55504a";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: CREAM,
          padding: 36,
        }}
      >
        {/* Ink frame inset on the paper */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            border: `6px solid ${INK}`,
            borderRadius: 28,
            backgroundColor: PAPER,
            padding: "44px 56px 40px",
          }}
        >
          {/* Header row */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                fontSize: 30,
                fontWeight: 800,
                letterSpacing: 8,
                color: INK,
              }}
            >
              CODE TRIBUNAL
            </div>
            <div
              style={{
                display: "flex",
                border: `3px solid ${INK}`,
                borderRadius: 10,
                padding: "6px 14px",
                fontSize: 17,
                fontWeight: 700,
                letterSpacing: 4,
                color: INK,
                backgroundColor: "#ffd23f",
              }}
            >
              INTENT-CONFORMANCE COURT
            </div>
          </div>

          {/* Middle: headline + stamp */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 40,
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                maxWidth: 720,
              }}
            >
              <div
                style={{
                  display: "flex",
                  fontSize: 72,
                  fontWeight: 800,
                  lineHeight: 1.08,
                  letterSpacing: -1.5,
                  color: INK,
                }}
              >
                Did the code build what the ticket asked for?
              </div>

              {/* Trust meter */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  marginTop: 38,
                  width: 560,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-end",
                    marginBottom: 10,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      fontSize: 19,
                      fontWeight: 700,
                      letterSpacing: 4,
                      color: MUTED,
                    }}
                  >
                    TRUST SCORE
                  </div>
                  <div
                    style={{
                      display: "flex",
                      fontSize: 32,
                      fontWeight: 800,
                      color: WARNING,
                    }}
                  >
                    61/100
                  </div>
                </div>
                <div
                  style={{
                    display: "flex",
                    width: "100%",
                    height: 30,
                    border: `4px solid ${INK}`,
                    borderRadius: 15,
                    backgroundColor: CREAM,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      width: "61%",
                      height: "100%",
                      backgroundImage: `linear-gradient(90deg, ${DANGER}, ${WARNING})`,
                    }}
                  />
                </div>
              </div>
            </div>

            {/* BLOCK stamp */}
            <div
              style={{
                display: "flex",
                width: 230,
                height: 230,
                borderRadius: 115,
                border: `10px solid ${DANGER}`,
                backgroundColor: "#fbe7e9",
                alignItems: "center",
                justifyContent: "center",
                transform: "rotate(-12deg)",
                boxShadow: `10px 10px 0 ${INK}`,
              }}
            >
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 190,
                  height: 190,
                  borderRadius: 95,
                  border: `4px solid ${DANGER}`,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    fontSize: 16,
                    fontWeight: 700,
                    letterSpacing: 6,
                    color: DANGER,
                  }}
                >
                  TRIBUNAL
                </div>
                <div
                  style={{
                    display: "flex",
                    fontSize: 52,
                    fontWeight: 800,
                    letterSpacing: 4,
                    color: DANGER,
                  }}
                >
                  BLOCK
                </div>
                <div
                  style={{
                    display: "flex",
                    fontSize: 15,
                    fontWeight: 700,
                    letterSpacing: 3,
                    color: DANGER,
                  }}
                >
                  DOES NOT CONFORM
                </div>
              </div>
            </div>
          </div>

          {/* Footer row */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                fontSize: 20,
                fontWeight: 700,
                letterSpacing: 5,
                color: INK,
              }}
            >
              CLI · MCP · WEB
            </div>
            <div
              style={{
                display: "flex",
                border: `3px solid ${INK}`,
                borderRadius: 10,
                padding: "8px 16px",
                fontSize: 19,
                fontWeight: 700,
                letterSpacing: 1,
                color: INK,
                backgroundColor: "#ffffff",
                boxShadow: `4px 4px 0 ${INK}`,
              }}
            >
              uvx --from code-tribunal tribunal-mcp
            </div>
          </div>
        </div>
      </div>
    ),
    size,
  );
}
