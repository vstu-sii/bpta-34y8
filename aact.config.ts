import type { AactConfig } from "aact";

const config: AactConfig = {
  source: { type: "plantuml", path: "./docs/architecture/c4-container.puml" },
  rules: {
    acyclic: true,
    dbPerService: true,
    cohesion: true,
    commonReuse: true,
    acl: true,
    // One API process, no separately deployed gateway in this MVP.
    apiGateway: false,
    // Repository is a component inside app, not a process (ADR-001).
    crud: false,
    // No measured stability labels yet; revisit after MVP changes.
    stableDependencies: false,
  },
};
export default config;
